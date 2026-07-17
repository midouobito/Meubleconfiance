"""
scraper/page_parser.py – DOM extraction logic for Facebook public pages.

Extracts posts from the page feed, parses:
  - post_id, post_url, post_text
  - published_at  (from <time> elements or heuristic patterns)
  - media_type    (text / image / video / reel / link)
  - media_urls    (image src or video src list)
  - likes_count, shares_count, comments_count

Facebook's DOM is heavily obfuscated and changes frequently. This module
uses a layered approach:
  1. Standard semantic selectors
  2. Aria-role fallbacks
  3. Regex patterns for post IDs embedded in URLs
"""
from __future__ import annotations

import asyncio
import logging
import re
from datetime import datetime, timezone
from typing import Any
from urllib.parse import urljoin

from playwright.async_api import Page

logger = logging.getLogger(__name__)

# ── Regex helpers ─────────────────────────────────────────────────────────────
_POST_ID_FROM_URL = re.compile(
    r"(?:posts|videos|photos|reel|permalink)/(\d+)|pfbid([A-Za-z0-9]+)"
)
_STORY_ID_PATTERN = re.compile(r"story_fbid=(\d+)")
_COUNT_PATTERN = re.compile(r"([\d,.]+[KkMm]?)")

FB_BASE = "https://www.facebook.com"


# ── Helper: parse human-friendly counts (e.g. "1.2K", "3M") ─────────────────
def _parse_count(raw: str) -> int:
    """Convert '1.2K', '3M', '456' → int."""
    raw = raw.replace(",", "").strip()
    match = _COUNT_PATTERN.search(raw)
    if not match:
        return 0
    token = match.group(1).upper()
    try:
        if token.endswith("K"):
            return int(float(token[:-1]) * 1_000)
        if token.endswith("M"):
            return int(float(token[:-1]) * 1_000_000)
        return int(float(token))
    except ValueError:
        return 0


def _extract_post_id(url: str) -> str:
    """Extract a stable post ID from a Facebook URL."""
    # Try story_fbid first (most reliable)
    m = _STORY_ID_PATTERN.search(url)
    if m:
        return m.group(1)
    m = _POST_ID_FROM_URL.search(url)
    if m:
        return m.group(1) or m.group(2) or ""
    # Last resort: use last path segment
    parts = url.rstrip("/").split("/")
    return parts[-1] if parts else url


def _normalise_fb_url(href: str) -> str:
    """Make relative Facebook URLs absolute and strip tracking params."""
    if not href.startswith("http"):
        href = urljoin(FB_BASE, href)
    # Strip ?__cft__... and similar tracking noise
    return href.split("?")[0]


# ── Core parser ───────────────────────────────────────────────────────────────

async def extract_posts(page: Page, page_name: str, max_posts: int) -> list[dict[str, Any]]:
    """
    Scroll through the Facebook page feed and return a list of parsed post dicts.

    Args:
        page:       Playwright Page already navigated to the FB page URL.
        page_name:  The target page's username / slug.
        max_posts:  Stop collecting after this many posts (0 = unlimited).

    Returns:
        List of post dicts ready for DB insertion.
    """
    posts: list[dict[str, Any]] = []
    seen_ids: set[str] = set()

    logger.info("Starting post extraction for page '%s' (max=%d)", page_name, max_posts)

    # Iterate article elements in the feed
    # Facebook renders posts as <div role="article"> or <article> tags
    feed_selectors = [
        'div[role="feed"] > div',
        'div[data-pagelet="FeedUnit_0"]',
        'div[role="article"]',
    ]

    for attempt in range(30):  # max 30 scroll rounds
        for feed_sel in feed_selectors:
            try:
                articles = await page.query_selector_all(feed_sel)
                if articles:
                    break
            except Exception:
                articles = []

        articles = await page.query_selector_all('div[role="article"]')

        for article in articles:
            if max_posts and len(posts) >= max_posts:
                logger.info("Reached max_posts limit (%d). Stopping.", max_posts)
                return posts

            try:
                post_data = await _parse_article(article, page_name)
            except Exception as exc:
                logger.warning("Failed to parse an article element: %s", exc)
                continue

            if not post_data or not post_data.get("post_id"):
                continue

            if post_data["post_id"] in seen_ids:
                continue  # duplicate in current scroll window

            seen_ids.add(post_data["post_id"])
            posts.append(post_data)
            logger.info(
                "[%d] Collected post %s – %s",
                len(posts),
                post_data["post_id"],
                post_data["media_type"],
            )

        if max_posts and len(posts) >= max_posts:
            break

        # Scroll down and wait for new content to load
        await page.evaluate("window.scrollBy(0, window.innerHeight * 1.5)")
        await asyncio.sleep(3)

        # Detect end-of-feed
        end_markers = await page.query_selector_all(
            'span:has-text("End of results"), div:has-text("No more posts")'
        )
        if end_markers:
            logger.info("End-of-feed detected. Stopping scroll.")
            break

    logger.info("Extraction complete. %d posts collected.", len(posts))
    return posts


async def _parse_article(article, page_name: str) -> dict[str, Any] | None:
    """Parse a single <div role='article'> element into a post dict."""

    # ── Post URL & ID ─────────────────────────────────────────────────────────
    post_url = ""
    post_id = ""

    # Look for a timestamp link (most reliable source of the post permalink)
    time_links = await article.query_selector_all("a[href*='/posts/'], a[href*='/videos/'], "
                                                   "a[href*='/photos/'], a[href*='/reel/'], "
                                                   "a[href*='story_fbid']")
    for link in time_links:
        href = await link.get_attribute("href") or ""
        if href and ("posts" in href or "videos" in href or "photos" in href
                     or "reel" in href or "story_fbid" in href):
            post_url = _normalise_fb_url(href)
            post_id = _extract_post_id(href)
            break

    if not post_id:
        # Fallback: try data-ft attribute
        data_ft = await article.get_attribute("data-ft") or ""
        m = re.search(r'"top_level_post_id":(\d+)', data_ft)
        if m:
            post_id = m.group(1)

    if not post_id:
        return None

    # ── Post text ─────────────────────────────────────────────────────────────
    post_text = ""
    text_selectors = [
        'div[data-ad-comet-preview="message"]',
        'div[data-ad-preview="message"]',
        'div[class*="userContent"]',
        'span[dir="auto"]',
    ]
    for sel in text_selectors:
        el = await article.query_selector(sel)
        if el:
            post_text = (await el.inner_text()).strip()
            if post_text:
                break

    # ── Published at ─────────────────────────────────────────────────────────
    published_at: datetime | None = None
    time_el = await article.query_selector("time[datetime]")
    if time_el:
        dt_str = await time_el.get_attribute("datetime") or ""
        try:
            published_at = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
        except ValueError:
            pass

    if not published_at:
        published_at = datetime.now(tz=timezone.utc)

    # ── Media type & URLs ─────────────────────────────────────────────────────
    media_type = "text"
    media_urls: list[str] = []

    # Video / Reel
    video_els = await article.query_selector_all("video[src], video source[src]")
    if video_els:
        media_type = "video"
        for v in video_els:
            src = await v.get_attribute("src") or ""
            if src and src not in media_urls:
                media_urls.append(src)

    # Check for reel indicator in URL
    if "reel" in post_url:
        media_type = "reel"

    # Images (only if no video found)
    if media_type == "text":
        img_els = await article.query_selector_all("img[src]")
        candidate_imgs = []
        for img in img_els:
            src = await img.get_attribute("src") or ""
            # Skip profile/avatar images (small square images < 100px or fbcdn avatar paths)
            alt = await img.get_attribute("alt") or ""
            width_attr = await img.get_attribute("width") or "0"
            if (
                src
                and "fbcdn.net" in src
                and "profile" not in src.lower()
                and src not in candidate_imgs
                and int(width_attr or 0) >= 200
            ):
                candidate_imgs.append(src)
        if candidate_imgs:
            media_type = "image"
            media_urls = candidate_imgs

    # Shared links
    if media_type == "text":
        link_el = await article.query_selector('a[href*="l.facebook.com"]')
        if link_el:
            media_type = "link"

    # ── Engagement counts ─────────────────────────────────────────────────────
    likes_count = 0
    shares_count = 0
    comments_count = 0

    # Reaction count  – Facebook uses aria-label like "234 people reacted"
    reaction_el = await article.query_selector('[aria-label*="reaction"], [aria-label*="people reacted"]')
    if not reaction_el:
        reaction_el = await article.query_selector('span[data-testid="UFI2ReactionsCount/root"]')
    if reaction_el:
        raw = await reaction_el.inner_text()
        likes_count = _parse_count(raw)

    # Comment count
    comment_el = await article.query_selector(
        'span:has-text("comment"), span:has-text("Comment")'
    )
    if comment_el:
        raw = await comment_el.inner_text()
        comments_count = _parse_count(raw)

    # Share count
    share_el = await article.query_selector(
        'span:has-text("share"), span:has-text("Share")'
    )
    if share_el:
        raw = await share_el.inner_text()
        shares_count = _parse_count(raw)

    return {
        "post_id": post_id,
        "page_name": page_name,
        "post_text": post_text,
        "post_url": post_url,
        "published_at": published_at.isoformat(),
        "media_type": media_type,
        "media_urls": media_urls,
        "stored_media": [],  # filled in by media_handler
        "likes_count": likes_count,
        "shares_count": shares_count,
        "comments_count": comments_count,
        "scraped_at": datetime.now(tz=timezone.utc).isoformat(),
    }
