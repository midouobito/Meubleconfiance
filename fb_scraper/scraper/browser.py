"""
scraper/browser.py – Playwright browser lifecycle management.

Provides a context-manager that spins up a stealth Chromium browser
with human-like fingerprinting to avoid basic bot-detection on Facebook.
"""
from __future__ import annotations

import logging
import random
from contextlib import asynccontextmanager
from pathlib import Path
from typing import AsyncGenerator

from playwright.async_api import (
    Browser,
    BrowserContext,
    Page,
    Playwright,
    async_playwright,
)

import config

logger = logging.getLogger(__name__)

SESSION_FILE = Path(__file__).resolve().parent.parent / "browser_session" / "storage_state.json"

_VIEWPORTS = [
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1920, "height": 1080},
    {"width": 1280, "height": 800},
]
_LOCALES   = ["en-US", "en-GB", "fr-FR", "de-DE"]
_TIMEZONES = ["America/New_York", "Europe/London", "Europe/Paris", "Europe/Berlin"]


@asynccontextmanager
async def launch_browser() -> AsyncGenerator[tuple[Browser, BrowserContext, Page], None]:
    """Async context-manager that yields (browser, context, page)."""
    playwright: Playwright
    async with async_playwright() as playwright:
        viewport  = random.choice(_VIEWPORTS)
        locale    = random.choice(_LOCALES)
        timezone  = random.choice(_TIMEZONES)

        has_session = SESSION_FILE.exists()
        logger.info(
            "Launching Chromium – viewport=%dx%d  locale=%s  tz=%s  session=%s",
            viewport["width"], viewport["height"], locale, timezone,
            "loaded" if has_session else "NONE (run save_session.py first)",
        )

        browser: Browser = await playwright.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--lang=en-US,en",
            ],
        )

        ctx_kwargs = dict(
            user_agent=config.USER_AGENT,
            viewport=viewport,
            locale=locale,
            timezone_id=timezone,
            java_script_enabled=True,
            extra_http_headers={"Accept-Language": "en-US,en;q=0.9"},
        )
        if has_session:
            ctx_kwargs["storage_state"] = str(SESSION_FILE)

        context: BrowserContext = await browser.new_context(**ctx_kwargs)

        await context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', { get: () => undefined });
            Object.defineProperty(navigator, 'plugins',   { get: () => [1, 2, 3, 4, 5] });
            Object.defineProperty(navigator, 'languages', { get: () => ['en-US', 'en'] });
            window.chrome = { runtime: {} };
            """
        )

        page: Page = await context.new_page()

        async def _route_handler(route, request):
            if request.resource_type in ("font",):
                await route.abort()
            else:
                await route.continue_()

        await page.route("**/*", _route_handler)

        try:
            yield browser, context, page
        finally:
            logger.info("Closing browser.")
            await context.close()
            await browser.close()


async def human_scroll(page: Page, pause: float = 2.0, jitter: float = 1.0) -> None:
    """
    Scroll down the page by a random amount to mimic human behaviour.

    Args:
        page:   Playwright page object.
        pause:  Base pause in seconds between scrolls.
        jitter: Maximum additional random seconds added to pause.
    """
    import asyncio

    scroll_amount = random.randint(600, 1200)
    await page.evaluate(f"window.scrollBy(0, {scroll_amount})")
    sleep_time = pause + random.uniform(0, jitter)
    logger.debug("Scrolled %dpx – sleeping %.2fs", scroll_amount, sleep_time)
    await asyncio.sleep(sleep_time)


async def dismiss_cookie_banner(page: Page) -> None:
    """
    Attempt to close the Facebook cookie / login pop-up if it appears.
    These selectors are best-effort; Facebook changes them frequently.
    """
    selectors = [
        '[data-testid="cookie-policy-manage-dialog-accept-button"]',
        'button[title="Allow all cookies"]',
        'button[title="Accept All"]',
        '[aria-label="Close"]',
        'div[role="dialog"] button:first-child',
    ]
    for selector in selectors:
        try:
            btn = page.locator(selector).first
            if await btn.is_visible(timeout=2000):
                await btn.click()
                logger.debug("Dismissed banner via selector: %s", selector)
                return
        except Exception:
            continue
    logger.debug("No cookie/login banner found to dismiss.")
