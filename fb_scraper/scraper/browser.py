"""
scraper/browser.py – Playwright browser lifecycle management.

Provides a context-manager that spins up a stealth Chromium browser
with human-like fingerprinting to avoid basic bot-detection on Facebook.
"""
from __future__ import annotations

import logging
import random
from contextlib import asynccontextmanager
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

# ── List of realistic viewports to rotate ────────────────────────────────────
_VIEWPORTS = [
    {"width": 1366, "height": 768},
    {"width": 1440, "height": 900},
    {"width": 1920, "height": 1080},
    {"width": 1280, "height": 800},
]

# ── Realistic browser locale / timezone combos ────────────────────────────────
_LOCALES = ["en-US", "en-GB", "fr-FR", "de-DE"]
_TIMEZONES = ["America/New_York", "Europe/London", "Europe/Paris", "Europe/Berlin"]


@asynccontextmanager
async def launch_browser() -> AsyncGenerator[tuple[Browser, BrowserContext, Page], None]:
    """
    Async context-manager that yields (browser, context, page).

    Usage:
        async with launch_browser() as (browser, ctx, page):
            await page.goto(url)
    """
    playwright: Playwright
    async with async_playwright() as playwright:
        viewport = random.choice(_VIEWPORTS)
        locale = random.choice(_LOCALES)
        timezone = random.choice(_TIMEZONES)

        logger.info(
            "Launching Chromium – viewport=%dx%d  locale=%s  tz=%s",
            viewport["width"],
            viewport["height"],
            locale,
            timezone,
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

        context: BrowserContext = await browser.new_context(
            user_agent=config.USER_AGENT,
            viewport=viewport,
            locale=locale,
            timezone_id=timezone,
            java_script_enabled=True,
            # Pretend we accept cookies so the cookie banner is less aggressive
            extra_http_headers={
                "Accept-Language": "en-US,en;q=0.9",
            },
        )

        # ── Erase navigator.webdriver fingerprint ─────────────────────────────
        await context.add_init_script(
            """
            Object.defineProperty(navigator, 'webdriver', {
                get: () => undefined,
            });
            Object.defineProperty(navigator, 'plugins', {
                get: () => [1, 2, 3, 4, 5],
            });
            Object.defineProperty(navigator, 'languages', {
                get: () => ['en-US', 'en'],
            });
            window.chrome = { runtime: {} };
            """
        )

        page: Page = await context.new_page()

        # Block images and fonts on non-media requests to speed up page load
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
