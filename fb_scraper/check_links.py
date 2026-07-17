"""
check_links.py – Scan what kinds of post URLs are found in the captured HTML.
"""
import re
from pathlib import Path

html_file = Path("debug_output/page.html")
if not html_file.exists():
    print("page.html not found.")
    exit(1)

html = html_file.read_text(encoding="utf-8")

# Find all href links
hrefs = re.findall(r'href=["\']([^"\']+)["\']', html)
print(f"Total links: {len(hrefs)}")

post_links = []
for href in hrefs:
    if any(k in href for k in ["/posts/", "/videos/", "/photos/", "/reel/", "story_fbid", "permalink.php"]):
        clean = href.split("?")[0]
        post_links.append(clean)

print("\n--- Unique Post Links Found ---")
for l in sorted(list(set(post_links))):
    print(" ", l[:120])
