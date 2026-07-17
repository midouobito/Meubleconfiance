"""
db/supabase_client.py – Supabase database helpers.

Provides:
  - get_client()   → initialised Supabase client (singleton)
  - upsert_post()  → UPSERT a single post (update engagement on conflict)
  - upsert_posts() → Batch UPSERT with per-record error handling
"""
from __future__ import annotations

import logging
from typing import Any

from supabase import Client, create_client
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

import config

logger = logging.getLogger(__name__)

TABLE = "facebook_posts"

# ── Singleton client ──────────────────────────────────────────────────────────
_client: Client | None = None


def get_client() -> Client:
    """Return the Supabase client, creating it on first call."""
    global _client
    if _client is None:
        logger.info("Initialising Supabase client → %s", config.SUPABASE_URL)
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
    return _client


# ── Fields to UPDATE when a post_id already exists ───────────────────────────
_UPSERT_UPDATE_FIELDS = [
    "likes_count",
    "shares_count",
    "comments_count",
    "media_urls",
    "stored_media",
    "post_text",
    "scraped_at",
]


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    reraise=True,
)
def upsert_post(post: dict[str, Any]) -> dict[str, Any] | None:
    """
    UPSERT a single post record.

    On conflict with `post_id`, update the mutable fields (engagement counts,
    media URLs, text) but preserve the original `published_at` and `id`.

    Args:
        post: Dict matching the `facebook_posts` schema.

    Returns:
        The upserted row, or None if the operation failed.
    """
    client = get_client()
    try:
        result = (
            client.table(TABLE)
            .upsert(
                post,
                on_conflict="post_id",
                # Supabase upsert merges the provided columns only
                # `returning="representation"` gives us back the full row
                returning="representation",
            )
            .execute()
        )
        if result.data:
            logger.debug("Upserted post_id=%s", post.get("post_id"))
            return result.data[0]
        logger.warning("Upsert returned no data for post_id=%s", post.get("post_id"))
        return None

    except Exception as exc:
        logger.error("DB error upserting post_id=%s: %s", post.get("post_id"), exc)
        raise  # let tenacity retry


def upsert_posts(posts: list[dict[str, Any]]) -> tuple[int, int]:
    """
    Batch UPSERT a list of posts with per-record error isolation.

    Args:
        posts: List of post dicts.

    Returns:
        (success_count, failure_count) tuple.
    """
    success = 0
    failure = 0

    for post in posts:
        try:
            upsert_post(post)
            success += 1
        except Exception as exc:
            logger.error(
                "Permanently failed to upsert post_id=%s after retries: %s",
                post.get("post_id"),
                exc,
            )
            failure += 1

    logger.info(
        "Batch upsert complete: %d succeeded, %d failed out of %d total.",
        success,
        failure,
        len(posts),
    )
    return success, failure


def fetch_existing_post_ids(page_name: str) -> set[str]:
    """
    Fetch all post_ids already stored for a given page.
    Useful for incremental scraping (skip already-stored posts).

    Args:
        page_name: The Facebook page slug.

    Returns:
        Set of post_id strings already in the DB.
    """
    client = get_client()
    try:
        result = (
            client.table(TABLE)
            .select("post_id")
            .eq("page_name", page_name)
            .execute()
        )
        ids = {row["post_id"] for row in (result.data or [])}
        logger.info(
            "Fetched %d existing post IDs for page '%s'.", len(ids), page_name
        )
        return ids
    except Exception as exc:
        logger.error("Failed to fetch existing post IDs: %s", exc)
        return set()
