"""
import_cookies.py – Create the browser session state manually using cookies.

Find these in your Chrome browser where you are logged into Facebook:
  1. Open facebook.com
  2. Press F12 (Developer Tools)
  3. Go to the Application tab (or Storage tab in Firefox)
  4. Select Cookies -> https://www.facebook.com
  5. Copy the values for 'c_user' and 'xs'
"""
import json
from pathlib import Path

SESSION_DIR = Path("browser_session")
SESSION_DIR.mkdir(exist_ok=True)
STORAGE_FILE = SESSION_DIR / "storage_state.json"

def main():
    print("=" * 60)
    print("  Facebook Cookie Importer")
    print("=" * 60)
    print()
    
    c_user = input("Enter 'c_user' cookie value: ").strip()
    xs = input("Enter 'xs' cookie value: ").strip()
    
    if not c_user or not xs:
        print("Error: Both c_user and xs cookie values are required.")
        return

    # Basic Playwright storage state structure
    state = {
        "cookies": [
            {
                "name": "c_user",
                "value": c_user,
                "domain": ".facebook.com",
                "path": "/",
                "expires": 1818856280,
                "httpOnly": False,
                "secure": True,
                "sameSite": "None"
            },
            {
                "name": "xs",
                "value": xs,
                "domain": ".facebook.com",
                "path": "/",
                "expires": 1818856280,
                "httpOnly": True,
                "secure": True,
                "sameSite": "None"
            },
            {
                "name": "vpn",
                "value": "1",
                "domain": ".facebook.com",
                "path": "/",
                "expires": 1818856280,
                "httpOnly": False,
                "secure": True,
                "sameSite": "Lax"
            }
        ],
        "origins": []
    }

    with open(STORAGE_FILE, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)

    print()
    print(f"Successfully generated: {STORAGE_FILE}")
    print("You can now run: python main.py")

if __name__ == "__main__":
    main()
