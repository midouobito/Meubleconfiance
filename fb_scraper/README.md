# fb_scraper – Facebook → Supabase Pipeline

A production-ready, modular Python pipeline that:

1. Scrapes posts from any **public** Facebook page using Playwright (headless Chromium).
2. Parses text, timestamps, media URLs, and engagement counts.
3. Archives expiring Facebook media to a **Supabase Storage Bucket**.
4. Upserts everything into a **Supabase `facebook_posts`** table (no duplicates ever).

---

## Project Layout

```
fb_scraper/
├── .env.example          # copy to .env and fill in secrets
├── schema.sql            # Run once in Supabase SQL editor
├── requirements.txt
├── main.py               # Entry point – run this
├── config.py             # Centralised settings (reads .env)
├── scraper/
│   ├── __init__.py
│   ├── browser.py        # Playwright browser management
│   ├── page_parser.py    # DOM extraction logic
│   └── media_handler.py  # Download & upload media to Supabase Storage
├── db/
│   ├── __init__.py
│   └── supabase_client.py # Supabase UPSERT helpers
└── logs/                  # Auto-created at runtime
```

---

## Quick Start

### 1 – Create the Supabase table

Open **Supabase → SQL Editor** and paste the contents of `schema.sql`, then run it.

### 2 – Create the Storage bucket (optional but recommended)

In **Supabase → Storage**, create a bucket named `facebook-media` and set it to **Public**.  
Or uncomment the last lines of `schema.sql` and run them separately.

### 3 – Configure secrets

```bash
cp .env.example .env
# Edit .env with your SUPABASE_URL, SUPABASE_SERVICE_KEY, and FB_PAGE_URL
```

### 4 – Install dependencies

```bash
pip install -r requirements.txt
python -m playwright install chromium
```

### 5 – Run the scraper

```bash
# Scrape the page configured in .env
python main.py

# Or override the page at runtime
python main.py --page https://www.facebook.com/AdidasOriginals --max-posts 50
```

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `SUPABASE_URL` | Your Supabase project URL | **required** |
| `SUPABASE_SERVICE_KEY` | Service-role key (full access) | **required** |
| `FB_PAGE_URL` | Facebook page username or URL | **required** |
| `MAX_POSTS` | Posts to scrape per run (0 = all) | `20` |
| `SCROLL_PAUSE_SECONDS` | Pause between scrolls (seconds) | `3` |
| `ARCHIVE_MEDIA` | Upload media to Supabase Storage | `true` |
| `LOG_LEVEL` | `DEBUG / INFO / WARNING / ERROR` | `INFO` |
| `LOG_FILE` | Log file path | `logs/scraper.log` |

---

## Notes on Anti-Bot Measures

- The scraper uses a **real Chromium browser** with randomised user-agent and viewport to mimic human behaviour.
- Scrolling is paced with configurable `SCROLL_PAUSE_SECONDS` plus random jitter.
- For heavy-duty usage (100+ pages/day), consider rotating residential proxies via Playwright's proxy option in `browser.py`.

---

## Media URL Expiry

Facebook CDN URLs expire within hours. The pipeline:

1. Downloads media immediately after scraping.
2. Uploads files to your Supabase Storage bucket `facebook-media`.
3. Stores the **permanent Supabase CDN URL** in `stored_media[]` alongside the original URL in `media_urls[]`.

Set `ARCHIVE_MEDIA=false` in `.env` to skip this step (original URLs will expire).
