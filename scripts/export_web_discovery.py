#!/usr/bin/env python3
"""Free cloud web/news discovery via Google News RSS.

This produces candidates only. Important claims must be verified against the
original publisher or official source before inclusion in the daily report.
"""
import email.utils
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import urlencode
from xml.etree import ElementTree as ET
from zoneinfo import ZoneInfo

import requests

JST = ZoneInfo("Asia/Tokyo")
OUT = Path("cloud-output/web-discovery-latest.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

QUERIES = [
    {
        "id": "us_core_ai",
        "q": '"OpenAI" OR "Anthropic" OR "Google DeepMind" OR "xAI" artificial intelligence when:1d',
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    },
    {
        "id": "agents_tools",
        "q": '"AI agent" OR "computer use" OR "AI coding" OR "AI safety" when:1d',
        "hl": "en-US",
        "gl": "US",
        "ceid": "US:en",
    },
    {
        "id": "china_ai",
        "q": '人工智能 OR 大模型 OR 智能体 OR DeepSeek OR 通义千问 OR MiniMax when:1d',
        "hl": "zh-CN",
        "gl": "CN",
        "ceid": "CN:zh-Hans",
    },
    {
        "id": "japan_ai",
        "q": '生成AI OR AIエージェント OR OpenAI OR Anthropic OR Gemini when:1d',
        "hl": "ja",
        "gl": "JP",
        "ceid": "JP:ja",
    },
]

HEADERS = {
    "User-Agent": "ai-daily-news-discovery/1.0 (+read-only; candidate discovery)"
}


def parse_date(value):
    if not value:
        return None
    try:
        dt = email.utils.parsedate_to_datetime(value)
        if dt and not dt.tzinfo:
            dt = dt.replace(tzinfo=timezone.utc)
        return dt
    except Exception:
        return None


now = datetime.now(JST)
prev = now.date() - timedelta(days=1)
start = datetime(prev.year, prev.month, prev.day, tzinfo=JST)
base = {
    "schema": "ai-daily-news.web-discovery.v1",
    "generated_at": now.isoformat(),
    "window_start": start.isoformat(),
    "window_end": now.isoformat(),
    "write_actions": "NONE",
    "scope": "GOOGLE_NEWS_RSS_CANDIDATES_NOT_FULL_WEB",
    "candidate_only": True,
    "verification_required": True,
    "expected_queries": len(QUERIES),
}

statuses = []
items_by_key = {}

for qcfg in QUERIES:
    params = {
        "q": qcfg["q"],
        "hl": qcfg["hl"],
        "gl": qcfg["gl"],
        "ceid": qcfg["ceid"],
    }
    url = "https://news.google.com/rss/search?" + urlencode(params)
    try:
        resp = requests.get(url, headers=HEADERS, timeout=25)
        resp.raise_for_status()
        root = ET.fromstring(resp.content)
        rows = root.findall("./channel/item")
        in_window = 0
        for row in rows[:60]:
            title = (row.findtext("title") or "").strip()
            link = (row.findtext("link") or "").strip()
            pub = parse_date(row.findtext("pubDate"))
            source_el = row.find("source")
            source = (source_el.text or "").strip() if source_el is not None and source_el.text else ""
            if not title or not link or pub is None:
                continue
            pub_jst = pub.astimezone(JST)
            if not (start <= pub_jst <= now):
                continue
            in_window += 1
            key = link
            existing = items_by_key.get(key)
            if existing:
                if qcfg["id"] not in existing["matched_queries"]:
                    existing["matched_queries"].append(qcfg["id"])
                continue
            items_by_key[key] = {
                "title": title,
                "url": link,
                "publisher": source,
                "source_type": "google_news_rss_discovery",
                "published": pub.isoformat(),
                "matched_queries": [qcfg["id"]],
            }

        statuses.append({
            "id": qcfg["id"],
            "ok": True,
            "returned": len(rows),
            "in_window": in_window,
            "source_url": url,
        })
    except Exception as exc:
        statuses.append({
            "id": qcfg["id"],
            "ok": False,
            "error": f"{type(exc).__name__}: {str(exc)[:300]}",
            "source_url": url,
        })

ok = sum(1 for s in statuses if s["ok"])
coverage = "COMPLETE" if ok == len(QUERIES) else ("FAILED" if ok == 0 else "PARTIAL")
items = sorted(items_by_key.values(), key=lambda x: x["published"], reverse=True)

payload = {
    **base,
    "coverage": coverage,
    "successful_queries": ok,
    "queries": statuses,
    "items": items,
}
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print("WEB_DISCOVERY_EXPORT", coverage, ok, "/", len(QUERIES), len(items))
