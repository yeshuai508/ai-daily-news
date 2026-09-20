#!/usr/bin/env python3
import json
import re
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
from bs4 import BeautifulSoup

OUT = Path("cloud-output/github-trending-latest.json")
OUT.parent.mkdir(parents=True, exist_ok=True)
SOURCE = "https://github.com/trending?since=daily"

def write(payload):
    OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

now = datetime.now(ZoneInfo("Asia/Tokyo"))
base = {
    "schema": "ai-daily-news.github-trending.v1",
    "generated_at": now.isoformat(),
    "source_url": SOURCE,
    "range": "today",
    "write_actions": "NONE",
}
try:
    r = requests.get(
        SOURCE,
        timeout=25,
        headers={
            "User-Agent": "ai-daily-news-cloud-collector/1.0",
            "Accept": "text/html,application/xhtml+xml",
        },
    )
    r.raise_for_status()
    soup = BeautifulSoup(r.text, "html.parser")
    rows = []
    for article in soup.select("article.Box-row"):
        h2 = article.select_one("h2 a")
        if not h2:
            continue
        href = (h2.get("href") or "").strip()
        if not re.fullmatch(r"/[^/\s]+/[^/\s]+", href):
            continue
        repo = href.strip("/")
        desc_el = article.select_one("p")
        language_el = article.select_one('[itemprop="programmingLanguage"]')
        stars_today = None
        for el in article.select("span"):
            txt = " ".join(el.stripped_strings)
            m = re.search(r"([\d,]+)\s+stars?\s+today", txt, re.I)
            if m:
                stars_today = int(m.group(1).replace(",", ""))
                break
        if stars_today is None:
            continue
        rows.append({
            "rank": len(rows) + 1,
            "repository": repo,
            "url": f"https://github.com/{repo}",
            "description": " ".join(desc_el.stripped_strings) if desc_el else "",
            "language": language_el.get_text(" ", strip=True) if language_el else None,
            "stars_today": stars_today,
        })
        if len(rows) == 3:
            break
    if len(rows) != 3:
        raise RuntimeError(f"expected 3 parseable Trending rows, got {len(rows)}")
    write({**base, "coverage": "COMPLETE", "top3": rows})
except Exception as e:
    write({**base, "coverage": "FAILED", "error": f"{type(e).__name__}: {e}", "top3": []})
