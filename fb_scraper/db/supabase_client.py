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

import re

logger = logging.getLogger(__name__)

TABLE = "products"

# ── Singleton client ──────────────────────────────────────────────────────────
_client: Client | None = None


def get_client() -> Client:
    """Return the Supabase client, creating it on first call."""
    global _client
    if _client is None:
        logger.info("Initialising Supabase client → %s", config.SUPABASE_URL)
        _client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
    return _client

def _map_to_product(post: dict[str, Any]) -> dict[str, Any]:
    text = post.get("post_text") or ""
    
    # Extract price
    price = 0
    clean_text = text.replace(' ', '')
    price_match = re.search(r'([0-9]+)000(?:دج|DA|da)', clean_text, re.IGNORECASE)
    if price_match:
        try:
            price = int(price_match.group(1)) * 1000
        except ValueError:
            pass

    # Basic category extraction
    lower_text = text.lower()
    cat = "ديكور وإكسسوارات"
    if 'صالون' in lower_text or 'salon' in lower_text: cat = 'صالونات'
    elif 'غرفة نوم' in lower_text or 'chambre' in lower_text: cat = 'غرف نوم'
    elif 'طاولة' in lower_text or 'table' in lower_text: cat = 'طاولات وكراسي'
    elif 'مطبخ' in lower_text or 'cuisine' in lower_text: cat = 'مطابخ'
    elif 'مكتب' in lower_text or 'bureau' in lower_text: cat = 'مكاتب'

    name = text.split('\n')[0].strip() if text else 'Produit Facebook'
    if not name:
        name = 'Produit Facebook'

    images = post.get("stored_media", [])
    if not images:
        images = post.get("media_urls", [])

    likes = post.get("likes_count", 0)
    badge = f"{likes} 👍" if likes > 0 else None

    return {
        "fb_post_id": post.get("post_id"),
        "name": name,
        "description": text,
        "price": price,
        "category": cat,
        "images": images,
        "badge": badge,
        "original_url": post.get("post_url"),
    }


@retry(
    retry=retry_if_exception_type(Exception),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=8),
    reraise=True,
)
def upsert_post(post: dict[str, Any]) -> dict[str, Any] | None:
    """
    UPSERT a single post record into the products table.
    """
    client = get_client()
    product_data = _map_to_product(post)
    
    try:
        result = (
            client.table(TABLE)
            .upsert(
                product_data,
                on_conflict="fb_post_id",
                returning="representation",
            )
            .execute()
        )
        if result.data:
            logger.debug("Upserted product for post_id=%s", post.get("post_id"))
            return result.data[0]
        logger.warning("Upsert returned no data for post_id=%s", post.get("post_id"))
        return None

    except Exception as exc:
        logger.error("DB error upserting post_id=%s: %s", post.get("post_id"), exc)
        raise  # let tenacity retry


def upsert_posts(posts: list[dict[str, Any]]) -> tuple[int, int]:
    """
    Batch UPSERT a list of posts with per-record error isolation.
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
    Fetch all fb_post_ids already stored.
    """
    client = get_client()
    try:
        result = (
            client.table(TABLE)
            .select("fb_post_id")
            .not_.is_("fb_post_id", "null")
            .execute()
        )
        ids = {row["fb_post_id"] for row in (result.data or []) if row.get("fb_post_id")}
        logger.info("Fetched %d existing post IDs.", len(ids))
        return ids
    except Exception as exc:
        logger.error("Failed to fetch existing post IDs: %s", exc)
        return set()
