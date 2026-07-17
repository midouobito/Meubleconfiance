"""
extract_cookies.py – Automated session extractor for Windows.

Locates Google Chrome and Microsoft Edge browser profile directories,
reads and decrypts their cookie databases using Windows DPAPI and AES-GCM,
extracts active Facebook session cookies (c_user, xs, etc.),
and saves them directly into the Playwright storage_state.json format.
"""
from __future__ import annotations

import base64
import ctypes
import json
import logging
import os
import shutil
import sqlite3
import tempfile
from ctypes import wintypes
from pathlib import Path

# Setup logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("CookieExtractor")

# ── DPAPI Structs & Win32 API bindings ───────────────────────────────────────
class DATA_BLOB(ctypes.Structure):
    _fields_ = [
        ("cbData", wintypes.DWORD),
        ("pbData", ctypes.POINTER(ctypes.c_char))
    ]

def decrypt_dpapi(encrypted_data: bytes) -> bytes:
    """Decrypt data using Windows DPAPI (CryptUnprotectData)."""
    crypt32 = ctypes.windll.crypt32
    data_in = DATA_BLOB(len(encrypted_data), ctypes.create_string_buffer(encrypted_data))
    data_out = DATA_BLOB()
    
    success = crypt32.CryptUnprotectData(
        ctypes.byref(data_in),
        None,
        None,
        None,
        None,
        0,
        ctypes.byref(data_out)
    )
    
    if not success:
        raise OSError("CryptUnprotectData failed to decrypt the master key.")
        
    decrypted_bytes = ctypes.string_at(data_out.pbData, data_out.cbData)
    ctypes.windll.kernel32.LocalFree(data_out.pbData)
    return decrypted_bytes


def get_aes_key(local_state_path: Path) -> bytes | None:
    """Get browser AES-GCM key from Local State and decrypt it with DPAPI."""
    try:
        with open(local_state_path, "r", encoding="utf-8") as f:
            local_state = json.load(f)
        
        encrypted_key_b64 = local_state["os_crypt"]["encrypted_key"]
        encrypted_key = base64.b64decode(encrypted_key_b64)
        
        # Strip DPAPI prefix (first 5 bytes are "DPAPI")
        dpapi_data = encrypted_key[5:]
        return decrypt_dpapi(dpapi_data)
    except Exception as exc:
        logger.debug("Failed reading AES key from %s: %s", local_state_path, exc)
        return None


def decrypt_cookie(encrypted_val: bytes, aes_key: bytes) -> str:
    """Decrypt Chrome 80+ cookies using AES-256-GCM."""
    try:
        from cryptography.hazmat.primitives.ciphers.aead import AESGCM
        
        if not encrypted_val.startswith(b"v10") and not encrypted_val.startswith(b"v11"):
            # Try plain DPAPI fallback for older formats
            return decrypt_dpapi(encrypted_val).decode("utf-8", errors="ignore")
            
        nonce = encrypted_val[3:15]
        ciphertext = encrypted_val[15:]
        
        aesgcm = AESGCM(aes_key)
        decrypted = aesgcm.decrypt(nonce, ciphertext, None)
        return decrypted.decode("utf-8")
    except Exception as exc:
        logger.debug("Decryption error: %s", exc)
        return ""


def extract_from_profile(profile_dir: Path, browser_name: str) -> list[dict]:
    """Find and decrypt Facebook cookies in a browser profile."""
    # Chrome/Edge store cookies in Network/Cookies (modern) or Cookies (old)
    cookie_paths = [
        profile_dir / "Network" / "Cookies",
        profile_dir / "Cookies"
    ]
    
    cookies_db = None
    for p in cookie_paths:
        if p.exists():
            cookies_db = p
            break
            
    if not cookies_db:
        return []
        
    local_state_path = profile_dir.parent / "Local State"
    if not local_state_path.exists():
         return []
         
    aes_key = get_aes_key(local_state_path)
    if not aes_key:
        return []

    # Copy cookies file because it is locked if the browser is running
    temp_db = Path(tempfile.gettempdir()) / f"fb_temp_cookies_{browser_name}"
    try:
        shutil.copy2(cookies_db, temp_db)
    except Exception as exc:
        logger.debug("Failed to copy cookies DB: %s", exc)
        return []

    fb_cookies = []
    try:
        conn = sqlite3.connect(temp_db)
        cursor = conn.cursor()
        
        # Check database schema (some older/modified versions might have different columns)
        cursor.execute("PRAGMA table_info(cookies)")
        cols = {col[1] for col in cursor.fetchall()}
        
        query = (
            "SELECT host_key, name, path, is_secure, is_httponly, expires_utc, encrypted_value "
            "FROM cookies WHERE host_key LIKE '%facebook.com'"
        )
        cursor.execute(query)
        
        for row in cursor.fetchall():
            host_key, name, path, is_secure, is_httponly, expires_utc, encrypted_value = row
            val = decrypt_cookie(encrypted_value, aes_key)
            if not val:
                continue
                
            # Convert Chromium timestamp to UNIX epoch seconds
            # Windows/Chrome uses microseconds since Jan 1, 1601.
            expires = 0
            if expires_utc > 0:
                expires = (expires_utc / 1000000) - 11644473600
                
            fb_cookies.append({
                "name": name,
                "value": val,
                "domain": host_key,
                "path": path,
                "expires": expires,
                "httpOnly": bool(is_httponly),
                "secure": bool(is_secure),
                "sameSite": "None" if is_secure else "Lax"
            })
            
    except Exception as exc:
        logger.error("Database query failed on %s: %s", cookies_db, exc)
    finally:
        if conn:
            conn.close()
        try:
            os.remove(temp_db)
        except Exception:
            pass
            
    return fb_cookies


def main():
    appdata = Path(os.environ.get("LOCALAPPDATA", ""))
    if not appdata:
        logger.critical("LOCALAPPDATA env var is not set. Run this on Windows.")
        return

    # Paths to search for browser profiles
    browsers = {
        "Chrome": appdata / "Google" / "Chrome" / "User Data",
        "Edge": appdata / "Microsoft" / "Edge" / "User Data"
    }

    found_session_cookies = []

    for browser_name, user_data_path in browsers.items():
        if not user_data_path.exists():
            continue
            
        logger.info("Scanning %s profiles...", browser_name)
        
        # Scan Default profile and Profile 1, Profile 2, etc.
        profiles = ["Default"]
        for item in user_data_path.iterdir():
            if item.is_dir() and item.name.startswith("Profile"):
                profiles.append(item.name)
                
        for prof in profiles:
            prof_dir = user_data_path / prof
            if prof_dir.exists():
                logger.info("  Scanning profile '%s'...", prof)
                cookies = extract_from_profile(prof_dir, f"{browser_name}_{prof}")
                
                # Check if we got the core FB authentication cookies
                has_c_user = any(c["name"] == "c_user" for c in cookies)
                has_xs = any(c["name"] == "xs" for c in cookies)
                
                if has_c_user and has_xs:
                    logger.info("  --> Found Active Facebook Login Session!")
                    found_session_cookies = cookies
                    break
                    
        if found_session_cookies:
            break

    if not found_session_cookies:
        logger.error("Could not find any active Facebook session cookies in Chrome or Edge.")
        logger.error("Please open your Chrome or Edge browser, log in to Facebook, and re-run this script.")
        return

    # Save to storage_state.json
    dest = Path("browser_session") / "storage_state.json"
    dest.parent.mkdir(exist_ok=True)
    
    state = {
        "cookies": found_session_cookies,
        "origins": []
    }
    
    with open(dest, "w", encoding="utf-8") as f:
        json.dump(state, f, indent=2)
        
    logger.info("Successfully exported Facebook session state to %s", dest)


if __name__ == "__main__":
    main()
