"""
scraper/media_handler.py – Download Facebook media and archive it to Supabase Storage.

Facebook CDN URLs expire within hours (they embed short-lived tokens in query strings).
This module:
  1. Downloads each media file with httpx (with retries).
  2. Uploads it to a Supabase Storage bucket.
  3. Returns the permanent public URL of the uploaded file.

The permanent URL is stored in `stored_media[]` in the DB so the original
expiring URL in `media_urls[]` is kept for reference but the permanent one
is used going forward.
"""
from __future__ import annotations

import hashlib
import logging
import mimetypes
import os
import re
import tempfile
from pathlib import Path
from typing import Any

import httpx
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

import config

logger = logging.getLogger(__name__)

# ── Supabase Storage client (lazy import to avoid circular deps) ──────────────
_storage_client = None


def _get_storage():
    """Lazily initialise the Supabase storage client."""
    global _storage_client
    if _storage_client is None:
        from supabase import create_client
        client = create_client(config.SUPABASE_URL, config.SUPABASE_SERVICE_KEY)
        _storage_client = client.storage
    return _storage_client


# ── URL fingerprint (stable filename from URL) ────────────────────────────────
def _url_to_filename(url: str, suffix: str = "") -> str:
    """
    Derive a stable, filesystem-safe filename from a media URL.
    We hash the URL (without query string) so filenames are deterministic.
    """
    clean_url = url.split("?")[0]
    digest = hashlib.sha256(clean_url.encode()).hexdigest()[:16]
    if not suffix:
        # Try to guess from URL path
        path = clean_url.rsplit("/", 1)[-1]
        ext = Path(path).suffix or ".bin"
        suffix = ext
    return f"{digest}{suffix}"


@retry(
    retry=retry_if_exception_type((httpx.TransportError, httpx.TimeoutException)),
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True,
)
async def _download_file(url: str, client: httpx.AsyncClient) -> bytes:
    """Download a file from a URL with retry logic."""
    headers = {
        "User-Agent": config.USER_AGENT,
        "Referer": "https://www.facebook.com/",
    }
    response = await client.get(url, headers=headers, follow_redirects=True, timeout=30)
    response.raise_for_status()
    return response.content


def _guess_content_type(url: str, data: bytes) -> tuple[str, str]:
    """
    Guess MIME type and file extension from URL or raw bytes magic bytes.

    Returns:
        (mime_type, extension) e.g. ("image/jpeg", ".jpg")
    """
    clean_url = url.split("?")[0]
    mime, _ = mimetypes.guess_type(clean_url)
    if not mime:
        # Sniff from magic bytes
        if data[:4] == b"\x00\x00\x00\x18" or data[4:8] == b"ftyp":
            mime = "video/mp4"
        elif data[:2] == b"\xff\xd8":
            mime = "image/jpeg"
        elif data[:8] == b"\x89PNG\r\n\x1a\n":
            mime = "image/png"
        elif data[:6] in (b"GIF87a", b"GIF89a"):
            mime = "image/gif"
        elif data[:4] == b"RIFF" and data[8:12] == b"WEBP":
            mime = "image/webp"
        else:
            mime = "application/octet-stream"

    ext = mimetypes.guess_extension(mime) or ".bin"
    # mimetypes sometimes returns .jpeg instead of .jpg – normalise
    ext = {".jpeg": ".jpg", ".jpe": ".jpg"}.get(ext, ext)
    return mime, ext


async def archive_media_urls(
    media_urls: list[str],
    post_id: str,
    page_name: str,
) -> list[str]:
    """
    Download each URL and upload to Supabase Storage.

    Args:
        media_urls: List of original (possibly expiring) Facebook CDN URLs.
        post_id:    Used to organise files inside the bucket.
        page_name:  Sub-folder name inside the bucket.

    Returns:
        List of permanent public Supabase Storage URLs (same length as input).
        If a single file fails, its position is replaced with an empty string.
    """
    if not config.ARCHIVE_MEDIA or not media_urls:
        return []

    stored: list[str] = []
    storage = _get_storage()

    async with httpx.AsyncClient() as http_client:
        for idx, url in enumerate(media_urls):
            if not url:
                stored.append("")
                continue

            try:
                logger.debug("Downloading media [%d/%d]: %s", idx + 1, len(media_urls), url[:80])
                data = await _download_file(url, http_client)
                mime, ext = _guess_content_type(url, data)
                filename = _url_to_filename(url, ext)
                storage_path = f"{page_name}/{post_id}/{filename}"

                logger.debug(
                    "Uploading %s (%s, %.1f KB) → bucket/%s",
                    filename,
                    mime,
                    len(data) / 1024,
                    storage_path,
                )

                # Upload to Supabase Storage
                # upsert=True so re-runs don't raise a conflict error
                storage.from_(config.SUPABASE_STORAGE_BUCKET).upload(
                    path=storage_path,
                    file=data,
                    file_options={"content-type": mime, "upsert": "true"},
                )

                # Build the permanent public URL
                public_url = (
                    f"{config.SUPABASE_URL}/storage/v1/object/public/"
                    f"{config.SUPABASE_STORAGE_BUCKET}/{storage_path}"
                )
                stored.append(public_url)
                logger.info("Archived media → %s", public_url)

            except httpx.HTTPStatusError as exc:
                logger.error(
                    "HTTP %d downloading %s – skipping.",
                    exc.response.status_code,
                    url[:80],
                )
                stored.append("")
            except Exception as exc:
                logger.error("Failed to archive media %s: %s", url[:80], exc)
                stored.append("")

    return stored
