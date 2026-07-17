"""
main.py – Entry point for the Facebook → Supabase scraper pipeline.

Usage
-----
    # Use values from .env
    python main.py

    # Override at runtime
    python main.py --page https://www.facebook.com/AdidasOriginals --max-posts 50

Pipeline
--------
    1. Parse CLI args / .env configuration
    2. Validate environment (Supabase connectivity, required vars)
    3. Launch stealth Chromium browser
    4. Navigate to the target Facebook page
    5. Dismiss cookie / login banners
    6. Scroll and extract posts from the feed
    7. For each post: archive expiring media → Supabase Storage
    8. UPSERT all posts into the `facebook_posts` table
    9. Print a Rich summary table
"""
from __future__ import annotations

import argparse
import asyncio
import logging
import sys
from datetime import datetime, timezone
from typing import Any

# ── Internal modules (config must be imported first to set up logging) ────────
import config  # noqa: F401  – side-effect: sets up logging
from db.supabase_client import fetch_existing_post_ids, get_client, upsert_posts
from scraper.browser import dismiss_cookie_banner, launch_browser
from scraper.media_handler import archive_media_urls
from scraper.page_parser import MBASIC_BASE, extract_posts

logger = logging.getLogger(__name__)


# ── CLI ───────────────────────────────────────────────────────────────────────

def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape a public Facebook page and sync posts to Supabase."
    )
    parser.add_argument(
        "--page",
        default=config.FB_PAGE_URL,
        help="Facebook page URL or username (overrides FB_PAGE_URL in .env)",
    )
    parser.add_argument(
        "--max-posts",
        type=int,
        default=config.MAX_POSTS,
        help="Maximum number of posts to scrape (0 = unlimited)",
    )
    parser.add_argument(
        "--no-media",
        action="store_true",
        default=not config.ARCHIVE_MEDIA,
        help="Skip media archival to Supabase Storage",
    )
    parser.add_argument(
        "--incremental",
        action="store_true",
        default=False,
        help="Skip posts that are already in the database (faster re-runs)",
    )
    return parser.parse_args()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _normalise_page_url(page: str) -> tuple[str, str]:
    """
    Accept either a URL or a plain username and return (url, page_name).

    Examples:
        "CocaCola"                       → ("https://www.facebook.com/CocaCola", "CocaCola")
        "https://www.facebook.com/Meta"  → ("https://www.facebook.com/Meta", "Meta")
    """
    if page.startswith("http"):
        url = page.rstrip("/")
        name = url.rsplit("/", 1)[-1]
    else:
        name = page.strip("/")
        url = f"https://www.facebook.com/{name}"
    return url, name


def _validate_environment() -> None:
    """Quick smoke-test that Supabase credentials work before scraping."""
    logger.info("Validating Supabase connection…")
    try:
        client = get_client()
        # Cheap query – fetch zero rows just to test auth
        client.table("facebook_posts").select("id").limit(0).execute()
        logger.info("Supabase connection OK.")
    except Exception as exc:
        logger.critical(
            "Cannot connect to Supabase. Check SUPABASE_URL and SUPABASE_SERVICE_KEY.\n"
            "Error: %s",
            exc,
        )
        sys.exit(1)


def _print_summary(posts: list[dict[str, Any]], success: int, failure: int) -> None:
    """Print a Rich table summarising the run."""
    try:
        from rich.console import Console
        from rich.table import Table

        console = Console()
        table = Table(title="Scrape Summary", show_lines=True)
        table.add_column("#", style="dim", width=4)
        table.add_column("Post ID", style="cyan", no_wrap=True)
        table.add_column("Type", style="magenta")
        table.add_column("Likes", justify="right")
        table.add_column("Shares", justify="right")
        table.add_column("Published At", style="green")

        for i, p in enumerate(posts[:50], 1):  # cap at 50 rows in terminal
            table.add_row(
                str(i),
                p.get("post_id", "")[:20],
                p.get("media_type", ""),
                str(p.get("likes_count", 0)),
                str(p.get("shares_count", 0)),
                str(p.get("published_at", ""))[:19],
            )

        console.print(table)
        console.print(
            f"[bold green]OK: {success} upserted[/bold green]  "
            f"[bold red]FAIL: {failure} failed[/bold red]  "
            f"out of {len(posts)} scraped posts."
        )
    except ImportError:
        # Fallback if rich is not installed
        print(f"\n=== Scrape complete: {success} upserted, {failure} failed ===\n")


# ── Main pipeline ─────────────────────────────────────────────────────────────

async def run_pipeline(
    page_url: str,
    page_name: str,
    max_posts: int,
    archive_media: bool,
    incremental: bool,
) -> None:
    logger.info("=" * 60)
    logger.info("Pipeline START  %s", datetime.now(tz=timezone.utc).isoformat())
    logger.info("Target page  : %s", page_url)
    logger.info("Max posts    : %s", max_posts or "unlimited")
    logger.info("Archive media: %s", archive_media)
    logger.info("Incremental  : %s", incremental)
    logger.info("=" * 60)

    # ── 1. Pre-load existing IDs for incremental mode ─────────────────────────
    existing_ids: set[str] = set()
    if incremental:
        existing_ids = fetch_existing_post_ids(page_name)
        logger.info("Incremental mode: %d posts already in DB.", len(existing_ids))

    # ── 2. Browser session ────────────────────────────────────────────────────
    async with launch_browser() as (browser, ctx, page):
        # Navigate with saved session (run save_session.py first if not done)
        logger.info("Navigating to %s ...", page_url)
        try:
            await page.goto(page_url, wait_until="domcontentloaded", timeout=60_000)
        except Exception as exc:
            logger.critical("Navigation failed: %s", exc)
            return

        # Dismiss cookie / login overlay
        await dismiss_cookie_banner(page)

        # Wait for desktop content to load
        try:
            await page.wait_for_selector('div[role="article"]', timeout=20_000)
        except Exception:
            logger.warning("Feed selector not found – page may be private or unavailable.")

        # ── 3. Extract posts ──────────────────────────────────────────────────
        raw_posts = await extract_posts(page, page_name, max_posts)

    if not raw_posts:
        logger.warning("No posts extracted. Exiting.")
        return

    # ── 4. Filter already-stored posts (incremental) ──────────────────────────
    if incremental:
        before = len(raw_posts)
        raw_posts = [p for p in raw_posts if p["post_id"] not in existing_ids]
        logger.info(
            "Incremental filter: %d new posts (skipped %d already stored).",
            len(raw_posts),
            before - len(raw_posts),
        )

    if not raw_posts:
        logger.info("All scraped posts are already in the database. Nothing to insert.")
        return

    # ── 5. Archive media for each post ────────────────────────────────────────
    if archive_media:
        logger.info("Archiving media for %d posts…", len(raw_posts))
        for post in raw_posts:
            if post.get("media_urls"):
                try:
                    stored = await archive_media_urls(
                        post["media_urls"],
                        post["post_id"],
                        page_name,
                    )
                    post["stored_media"] = stored
                except Exception as exc:
                    logger.error(
                        "Media archive failed for post %s: %s", post["post_id"], exc
                    )
                    post["stored_media"] = []

    # ── 6. UPSERT into Supabase ───────────────────────────────────────────────
    logger.info("Upserting %d posts into Supabase…", len(raw_posts))
    success, failure = upsert_posts(raw_posts)

    # ── 7. Summary ────────────────────────────────────────────────────────────
    _print_summary(raw_posts, success, failure)
    logger.info("Pipeline END  %s", datetime.now(tz=timezone.utc).isoformat())


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    args = parse_args()

    if not args.page:
        print(
            "ERROR: No Facebook page specified.\n"
            "Set FB_PAGE_URL in .env or pass --page <url/username>."
        )
        sys.exit(1)

    page_url, page_name = _normalise_page_url(args.page)
    archive_media = not args.no_media

    _validate_environment()

    asyncio.run(
        run_pipeline(
            page_url=page_url,
            page_name=page_name,
            max_posts=args.max_posts,
            archive_media=archive_media,
            incremental=args.incremental,
        )
    )


if __name__ == "__main__":
    main()
