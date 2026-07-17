"""
debug_page.py – Snapshot the mbasic page HTML using the loaded session state.
"""
import asyncio
import json
from pathlib import Path
from playwright.async_api import async_playwright

URL = "https://mbasic.facebook.com/Meuble.Confiance.Batna.05"
SESSION_FILE = Path("browser_session") / "storage_state.json"
OUT = Path("debug_output")
OUT.mkdir(exist_ok=True)


async def main():
    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=True)
        
        ctx_kwargs = {
            "user_agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
            "viewport": {"width": 1280, "height": 800},
        }
        if SESSION_FILE.exists():
            ctx_kwargs["storage_state"] = str(SESSION_FILE)
            print("Session file found and loaded.")
        else:
            print("Warning: No session file found.")

        context = await browser.new_context(**ctx_kwargs)
        page = await context.new_page()

        print(f"Navigating to {URL} ...")
        await page.goto(URL, wait_until="domcontentloaded", timeout=60_000)
        await asyncio.sleep(5)

        # Save screenshot
        await page.screenshot(path=str(OUT / "screenshot.png"), full_page=True)
        print("Screenshot saved to debug_output/screenshot.png")

        # Save full HTML
        html = await page.content()
        (OUT / "page.html").write_text(html, encoding="utf-8")
        print("HTML saved to debug_output/page.html")

        print("Current URL:", page.url)
        print("Page Title:", await page.title())
        
        # Check elements count
        has_ft = await page.evaluate("() => document.querySelectorAll('[data-ft]').length")
        articles = await page.evaluate("() => document.querySelectorAll('article').length")
        anchors = await page.evaluate("() => document.querySelectorAll('a').length")
        
        print(f"Elements: data-ft={has_ft}, articles={articles}, links={anchors}")

        await browser.close()


asyncio.run(main())

