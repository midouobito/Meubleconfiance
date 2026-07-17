"""
config.py – Centralised settings loaded from the .env file.

All other modules import from here; nothing reads os.environ directly.
"""
from __future__ import annotations

import os
import logging
from pathlib import Path
from dotenv import load_dotenv

# ── Load .env ────────────────────────────────────────────────────────────────
# Walk up the directory tree to find the first .env file
_HERE = Path(__file__).resolve().parent
load_dotenv(_HERE / ".env", override=False)


def _require(key: str) -> str:
    """Return an env-var value or raise a clear error if it is missing."""
    value = os.getenv(key)
    if not value:
        raise EnvironmentError(
            f"Required environment variable '{key}' is not set. "
            f"Copy .env.example to .env and fill in your values."
        )
    return value


def _bool_env(key: str, default: bool = False) -> bool:
    """Parse a boolean environment variable."""
    raw = os.getenv(key, str(default)).strip().lower()
    return raw in ("1", "true", "yes", "on")


# ── Supabase ─────────────────────────────────────────────────────────────────
SUPABASE_URL: str = _require("SUPABASE_URL")
SUPABASE_SERVICE_KEY: str = _require("SUPABASE_SERVICE_KEY")
SUPABASE_STORAGE_BUCKET: str = os.getenv("SUPABASE_STORAGE_BUCKET", "facebook-media")

# ── Facebook target ───────────────────────────────────────────────────────────
FB_PAGE_URL: str = os.getenv("FB_PAGE_URL", "")

# ── Scraper behaviour ─────────────────────────────────────────────────────────
MAX_POSTS: int = int(os.getenv("MAX_POSTS", "20"))
SCROLL_PAUSE_SECONDS: float = float(os.getenv("SCROLL_PAUSE_SECONDS", "3"))
ARCHIVE_MEDIA: bool = _bool_env("ARCHIVE_MEDIA", default=True)

# ── Logging ───────────────────────────────────────────────────────────────────
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO").upper()
LOG_FILE: str = os.getenv("LOG_FILE", "logs/scraper.log")

# ── Browser fingerprint spoofing ──────────────────────────────────────────────
# Rotate these in .env if you hit rate limits
USER_AGENT: str = os.getenv(
    "USER_AGENT",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/125.0.0.0 Safari/537.36",
)
VIEWPORT_WIDTH: int = int(os.getenv("VIEWPORT_WIDTH", "1366"))
VIEWPORT_HEIGHT: int = int(os.getenv("VIEWPORT_HEIGHT", "768"))


# ── Logging setup (called once at import time) ────────────────────────────────
def _setup_logging() -> None:
    log_path = Path(LOG_FILE)
    log_path.parent.mkdir(parents=True, exist_ok=True)

    logging.basicConfig(
        level=getattr(logging, LOG_LEVEL, logging.INFO),
        format="%(asctime)s [%(levelname)s] %(name)s – %(message)s",
        datefmt="%Y-%m-%dT%H:%M:%S",
        handlers=[
            logging.FileHandler(log_path, encoding="utf-8"),
            logging.StreamHandler(),
        ],
    )


_setup_logging()
