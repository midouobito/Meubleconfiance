import asyncio
from playwright.async_api import async_playwright
import os

async def main():
    path = os.path.abspath("catalogue.html")
    url = f"file:///{path.replace(os.sep, '/')}"
    
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        page.on("console", lambda msg: print(f"CONSOLE: {msg.text}"))
        page.on("pageerror", lambda err: print(f"PAGE ERROR: {err}"))
        
        print("Navigating to", url)
        await page.goto(url)
        await page.wait_for_timeout(3000)
        await browser.close()

asyncio.run(main())
