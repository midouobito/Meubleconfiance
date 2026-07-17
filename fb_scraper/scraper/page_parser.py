"""
scraper/page_parser.py – DOM parser for Facebook Desktop Feed (www.facebook.com)

Parses posts directly from the desktop version of Facebook since authenticated
sessions are redirected to the full desktop site.

Extracts:
  - post_id (from links or feed container IDs)
  - post_text (from message containers)
  - published_at
  - media_type (text, image, video, reel, link)
  - media_urls
  - engagement counts (likes, comments, shares)
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin, urlparse, parse_qs

from playwright.async_api import Page

logger = logging.getLogger(__name__)

# Canonical domain base
FB_BASE = "https://www.facebook.com"
MBASIC_BASE = "https://mbasic.facebook.com" # kept for backwards compatibility in main imports

# Regex helpers
_STORY_ID = re.compile(r"story_fbid[=%]3D(\d+)|story_fbid=(\d+)")
_POST_ID = re.compile(r"/posts/(\d+)|/videos/(\d+)|/photos/\S+/(\d+)|/reel/(\d+)")
_COUNT_PATTERN = re.compile(r"([\d,.]+)\s*([KkMm]?)")


def _parse_count(raw: str) -> int:
    raw = raw.strip()
    if not raw:
        return 0
        
    # Find all numeric patterns (e.g. 187, 1.2K, 12,300)
    numbers = re.findall(r"(\d[\d,.]*\s*[KkMm]?)", raw)
    if not numbers:
        return 0
        
    total = 0
    for num_str in numbers:
        num_str = num_str.replace(",", "").replace(" ", "").upper()
        try:
            if num_str.endswith("K"):
                total += int(float(num_str[:-1]) * 1000)
            elif num_str.endswith("M"):
                total += int(float(num_str[:-1]) * 1000000)
            else:
                total += int(float(num_str))
        except ValueError:
            continue
            
    # If the string lists names (e.g. "Saa Lim et 187 autres personnes"), we add the named individuals
    if " et " in raw or " and " in raw:
        parts = re.split(r"\bet\b|\band\b", raw, maxsplit=1)
        if len(parts) > 1:
            names_part = parts[0]
            # Split names by commas or standard separators to count them
            names = [n.strip() for n in re.split(r",", names_part) if n.strip()]
            total += len(names)
            
    return total


def _extract_post_id(url: str) -> str:
    m = _STORY_ID.search(url)
    if m:
        return m.group(1) or m.group(2) or ""
    m = _POST_ID.search(url)
    if m:
        return next((g for g in m.groups() if g), "")
    # pfbid style: extract from query string
    qs = parse_qs(urlparse(url).query)
    if "id" in qs:
        return qs["id"][0]
    # last segment
    parts = url.rstrip("/").split("/")
    return parts[-1] if parts else ""


def _normalise_fb_url(href: str) -> str:
    if not href:
        return ""
    if not href.startswith("http"):
        href = urljoin(FB_BASE, href)
    return href.split("?")[0]


async def extract_posts(page: Page, page_name: str, max_posts: int) -> list[dict[str, Any]]:
    """
    Scroll and extract posts from the desktop Facebook page feed.
    """
    posts: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    logger.info("Extracting posts from desktop feed for '%s' (max=%d)", page_name, max_posts)

    # Scroll loop
    for scroll_round in range(1, 30):
        # On desktop, each post card is a div inside the timeline feed.
        # Common selector: role="article" or structured data-pagelet elements
        articles = await page.query_selector_all('div[role="article"]')
        logger.info("Scroll round %d: Found %d post elements on page.", scroll_round, len(articles))

        new_posts_found = 0
        for article in articles:
            if max_posts and len(posts) >= max_posts:
                logger.info("Reached max_posts limit. Stopping.")
                return posts

            try:
                post_data = await _parse_desktop_article(article, page_name)
            except Exception as exc:
                logger.debug("Failed parsing element: %s", exc)
                continue

            if not post_data or not post_data.get("post_id"):
                continue

            if post_data["post_id"] in seen_ids:
                # Still verify if engagement stats need to be updated (upsert logic handles this, but don't add to output twice in this run)
                continue

            seen_ids.add(post_data["post_id"])
            posts.append(post_data)
            new_posts_found += 1
            
            logger.info(
                "[%d] Loaded post: ID=%s  Type=%-6s  Likes=%-4d  Comments=%-4d  Shares=%-4d",
                len(posts),
                post_data["post_id"],
                post_data["media_type"],
                post_data["likes_count"],
                post_data["comments_count"],
                post_data["shares_count"]
            )

        if max_posts and len(posts) >= max_posts:
            break

        # Scroll down to load more content
        await page.evaluate("window.scrollBy(0, 1500)")
        await asyncio.sleep(4)

        # Detect feed end or login overlays
        no_more = await page.query_selector_all('span:has-text("Plus de publications"), span:has-text("End of results")')
        if no_more:
            logger.info("No more posts available (end of feed).")
            break

    logger.info("Extraction complete: %d posts collected.", len(posts))
    return posts


async def _parse_desktop_article(article, page_name: str) -> dict[str, Any] | None:
    """Parse a single desktop role='article' block."""
    
    # ── 1. Post ID and URL ──────────────────────────────────────────────────
    post_url = ""
    post_id = ""

    # Look for links that link to the post detail view (timestamps, permalinks, reels, photo links)
    links = await article.query_selector_all('a[href*="/posts/"], a[href*="/videos/"], a[href*="/photos/"], a[href*="/reel/"], a[href*="permalink.php"], a[href*="story_fbid"]')
    for link in links:
        href = await link.get_attribute("href") or ""
        if href:
            post_url = _normalise_fb_url(href)
            post_id = _extract_post_id(href)
            if post_id:
                break

    if not post_id:
        return None

    # ── 2. Text Content ──────────────────────────────────────────────────────
    post_text = ""
    # Text container usually has a dir="auto" attribute and is wrapped in post-message class styling
    text_els = await article.query_selector_all('div[dir="auto"]')
    for el in text_els:
        # Exclude comment containers, headers, author name, or action button texts
        text_content = (await el.inner_text()).strip()
        if len(text_content) > len(post_text) and not text_content.startswith("Commenter") and not text_content.startswith("Partager"):
            post_text = text_content

    # ── 3. Published Timestamp ────────────────────────────────────────────────
    published_at = datetime.now(tz=timezone.utc)
    # Desktop uses <a role="link"> containing a timestamp or a time element inside
    time_el = await article.query_selector("time")
    if time_el:
        dt_str = await time_el.get_attribute("datetime")
        if dt_str:
            try:
                published_at = datetime.fromtimestamp(int(dt_str), tz=timezone.utc)
            except ValueError:
                try:
                    published_at = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
                except ValueError:
                    pass

    # ── 4. Media Parsing ─────────────────────────────────────────────────────
    media_type = "text"
    media_urls: list[str] = []

    # Check for videos/reels
    video_els = await article.query_selector_all("video")
    if video_els or "/videos/" in post_url or "/reel/" in post_url:
        media_type = "reel" if "/reel/" in post_url else "video"
        for v in video_els:
            src = await v.get_attribute("src") or ""
            if src and not src.startswith("blob:") and src not in media_urls:
                media_urls.append(src)
                
    # Always extract available images (e.g. photos, video poster frames, reel covers)
    img_els = await article.query_selector_all("img")
    candidate_imgs = []
    for img in img_els:
        src = await img.get_attribute("src") or ""
        alt = await img.get_attribute("alt") or ""
        # Filter out avatars, emojis, icons, and small decoration assets
        if src and "fbcdn" in src and "emoji" not in src and "rsrc.php" not in src:
            # Skip small profile avatars or small UI buttons
            if "profile" not in src.lower() and "profile" not in alt.lower():
                # Avoid duplicates
                if src not in candidate_imgs:
                    candidate_imgs.append(src)
                    
    if candidate_imgs:
        # If it's a text post, change type to image
        if media_type == "text":
            media_type = "image"
        # Combine extracted images into media_urls
        for img_url in candidate_imgs:
            if img_url not in media_urls:
                media_urls.append(img_url)

    # ── 5. Engagement Metrics (Likes, Comments, Shares) ─────────────────────
    likes_count = 0
    comments_count = 0
    shares_count = 0

    # Likes selector (usually has a label containing reaction stats or is a sibling of the reaction icons)
    # Check text elements matching reaction summaries
    likes_el = await article.query_selector('span[class*="xt0psk2"], span[class*="x1n2onr6"] > span')
    if likes_el:
        likes_count = _parse_count(await likes_el.inner_text())
    else:
        # Fallback to scanning text patterns
        article_text = await article.inner_text()
        m = re.search(r"(\d[\d,.]*)\s*(?:likes|J'aime|reaction|personnes|autres)", article_text, re.IGNORECASE)
        if m:
            likes_count = _parse_count(m.group(1))

    # Comments and Shares
    # Find spans or links that mention "commentaires" (French) or "comments" (English)
    cmt_els = await article.query_selector_all('span:has-text("commentaire"), span:has-text("comment")')
    for cmt in cmt_els:
        txt = await cmt.inner_text()
        count = _parse_count(txt)
        if count > 0:
            comments_count = count
            break

    share_els = await article.query_selector_all('span:has-text("partage"), span:has-text("share")')
    for sh in share_els:
        txt = await sh.inner_text()
        count = _parse_count(txt)
        if count > 0:
            shares_count = count
            break

    return {
        "post_id": post_id,
        "page_name": page_name,
        "post_text": post_text,
        "post_url": post_url,
        "published_at": published_at.isoformat(),
        "media_type": media_type,
        "media_urls": media_urls,
        "stored_media": [],
        "likes_count": likes_count,
        "shares_count": shares_count,
        "comments_count": comments_count,
        "scraped_at": datetime.now(tz=timezone.utc).isoformat(),
    }
