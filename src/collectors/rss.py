"""RSS feed collector."""

import feedparser
import requests
import yaml
from datetime import datetime, timedelta, timezone

HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"}


def collect_rss(hours=24) -> list[dict]:
    """Fetch articles from RSS feeds published in the last N hours."""
    with open("config/feeds.yaml") as f:
        config = yaml.safe_load(f)

    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)
    items = []

    for feed_cfg in config.get("rss_feeds", []):
        name = feed_cfg["name"]
        url = feed_cfg["rss"]
        print(f"  Fetching RSS: {name}")
        try:
            resp = requests.get(url, headers=HEADERS, timeout=15)
            feed = feedparser.parse(resp.text)
            for entry in feed.entries:
                published = None
                if hasattr(entry, "published_parsed") and entry.published_parsed:
                    published = datetime(*entry.published_parsed[:6], tzinfo=timezone.utc)
                elif hasattr(entry, "updated_parsed") and entry.updated_parsed:
                    published = datetime(*entry.updated_parsed[:6], tzinfo=timezone.utc)

                if published and published < cutoff:
                    continue

                items.append({
                    "title": entry.get("title", ""),
                    "url": entry.get("link", ""),
                    "summary": entry.get("summary", "")[:1500],
                    "source": name,
                    "source_type": "rss",
                    "published": published.isoformat() if published else None,
                })
            print(f"    Got {len([i for i in items if i['source'] == name])} items")
        except Exception as e:
            print(f"    Error: {e}")

    return items
