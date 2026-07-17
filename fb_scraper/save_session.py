"""
save_session.py – Run this ONCE to log into Facebook and save your session.

Opens a VISIBLE browser window. Log in normally.
The script automatically detects when you are logged in and saves the session.

Usage:
    python save_session.py
"""
import asyncio
from pathlib import Path
from playwright.async_api import async_playwright

SESSION_DIR = Path("browser_session")
SESSION_DIR.mkdir(exist_ok=True)
STORAGE_FILE = SESSION_DIR / "storage_state.json"


async def main():
    print("=" * 60)
    print("  Facebook Session Saver")
    print("=" * 60)
    print()
    print("A browser window will open.")
    print("  --> Log into your Facebook account in that window.")
    print("  --> Wait until you see your Facebook feed/homepage.")
    print("  --> This script will save the session AUTOMATICALLY.")
    print()
    print("Do NOT close this terminal window.")
    print()

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=False,
            args=["--start-maximized"],
        )
        context = await browser.new_context(
            user_agent=(
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/125.0.0.0 Safari/537.36"
            ),
            viewport={"width": 1366, "height": 768},
        )
        page = await context.new_page()

        print("Opening Facebook...")
        await page.goto("https://www.facebook.com/login", wait_until="domcontentloaded")
        print()
        print(">> Log into Facebook in the browser window that just opened. <<")
        print("   Waiting for you to log in...")
        print()

        # Wait automatically until we are no longer on a login/checkpoint page
        # Timeout: 5 minutes
        try:
            await page.wait_for_function(
                """() => {
                    const url = window.location.href;
                    return !url.includes('/login') &&
                           !url.includes('/checkpoint') &&
                           !url.includes('/recover') &&
                           url.includes('facebook.com');
                }""",
                timeout=300_000,  # 5 minutes
            )
            print("Login detected! Saving session...")
        except Exception:
            print("Timed out waiting for login. Saving whatever session exists...")

        current_url = page.url
        print(f"Current URL: {current_url}")

        # Save the full browser storage state
        await context.storage_state(path=str(STORAGE_FILE))
        await browser.close()

    print()
    print(f"Session saved to: {STORAGE_FILE}")
    print()
    print("You can now run the scraper:")
    print("  python main.py")
    print()
    print("The session lasts until Facebook expires it (usually 30-90 days).")
    print("Re-run save_session.py if the scraper stops working.")


if __name__ == "__main__":
    asyncio.run(main())
