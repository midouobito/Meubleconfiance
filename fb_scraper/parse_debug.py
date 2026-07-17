"""
parse_debug.py – Inspect images in the cached debug page.
"""
import re
from pathlib import Path

html_file = Path("debug_output/page.html")
if not html_file.exists():
    print("No page.html found in debug_output.")
    exit(1)

html = html_file.read_text(encoding="utf-8")

# Extract all img src tags
srcs = re.findall(r'<img[^>]+src=["\']([^"\']+)["\']', html)
print(f"Found {len(srcs)} img src elements.")

# Print first 30 img sources that belong to Facebook CDN (fbcdn)
print("\n--- fbcdn images ---")
count = 0
for s in srcs:
    if "fbcdn" in s:
        # Clean escape chars
        s_clean = s.replace("&amp;", "&")
        print(f"[{count}] {s_clean[:120]}")
        count += 1
        if count >= 30:
            break
