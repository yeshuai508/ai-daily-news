#!/usr/bin/env python3
"""Read-only dynamic X discovery by expanding from the trusted core whitelist.

The core 16 accounts remain unchanged. This layer discovers external accounts
that the core accounts retweeted or mentioned during the reporting window, then
reads a small recent sample from those external accounts. No X write actions.
"""
import asyncio
import json
import os
import re
from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

from dotenv import load_dotenv
from twikit import Client

load_dotenv()

JST = ZoneInfo("Asia/Tokyo")
CORE_PATH = Path("cloud-output/x-latest.json")
OUT = Path("cloud-output/x-discovery-latest.json")
OUT.parent.mkdir(parents=True, exist_ok=True)

MAX_EXPANSION_ACCOUNTS = 10
MAX_TWEETS_PER_ACCOUNT = 20
HANDLE_RE = re.compile(r"@([A-Za-z0-9_]{1,15})")
RT_RE = re.compile(r"^RT\s+@([A-Za-z0-9_]{1,15})", re.I)


def created_at(tweet):
    value = getattr(tweet, "created_at", None)
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    if isinstance(value, str):
        return datetime.strptime(value, "%a %b %d %H:%M:%S %z %Y")
    raise ValueError("tweet created_at unavailable")


async def collect():
    now = datetime.now(JST)
    prev = now.date() - timedelta(days=1)
    start = datetime(prev.year, prev.month, prev.day, tzinfo=JST)

    base = {
        "schema": "ai-daily-news.x-discovery.v1",
        "generated_at": now.isoformat(),
        "window_start": start.isoformat(),
        "window_end": now.isoformat(),
        "write_actions": "NONE",
        "scope": "DYNAMIC_NETWORK_EXPANSION_FROM_CORE_X",
        "candidate_only": True,
        "verification_required": True,
        "collector_method": "core_retweet_mention_expansion",
        "max_expansion_accounts": MAX_EXPANSION_ACCOUNTS,
    }

    if not CORE_PATH.exists():
        return {**base, "coverage": "FAILED", "semantic_health": "FAILED",
                "expected_accounts": 0, "successful_accounts": 0,
                "targets": [], "items": [], "error": "core X cache missing"}

    core = json.loads(CORE_PATH.read_text(encoding="utf-8"))
    core_handles = {str(t.get("handle", "")).lower() for t in core.get("targets", [])}

    score = Counter()
    evidence = {}
    for item in core.get("items", []):
        text = str(item.get("summary") or "")
        rt = RT_RE.search(text)
        if rt:
            h = rt.group(1)
            if h.lower() not in core_handles:
                score[h] += 6
                evidence.setdefault(h.lower(), []).append(item.get("url"))
        for h in HANDLE_RE.findall(text):
            if h.lower() in core_handles:
                continue
            score[h] += 1
            evidence.setdefault(h.lower(), []).append(item.get("url"))

    ranked = [h for h, _ in score.most_common(MAX_EXPANSION_ACCOUNTS)]
    base["discovered_accounts"] = len(ranked)

    if not ranked:
        return {**base, "coverage": "EMPTY", "semantic_health": "SUSPECT_EMPTY",
                "expected_accounts": 0, "successful_accounts": 0,
                "targets": [], "items": [], "error": "no external handles surfaced by core accounts"}

    auth = os.getenv("X_AUTH_TOKEN")
    ct0 = os.getenv("X_CT0")
    if not auth or not ct0:
        return {**base, "coverage": "FAILED", "semantic_health": "FAILED",
                "expected_accounts": len(ranked), "successful_accounts": 0,
                "targets": [], "items": [], "error": "X read-only secrets are required"}

    client = Client("en-US", proxy=os.getenv("PROXY_URL"))
    client.set_cookies({"auth_token": auth, "ct0": ct0})

    core_urls = {str(i.get("url")) for i in core.get("items", [])}
    items_by_url = {}
    targets = []

    for h in ranked:
        try:
            user = await client.get_user_by_screen_name(h)
            tweets = await user.get_tweets("Tweets", count=MAX_TWEETS_PER_ACCOUNT)
            n = 0
            for tweet in tweets:
                try:
                    dt = created_at(tweet)
                except Exception:
                    continue
                if not (start <= dt.astimezone(JST) <= now):
                    continue
                text = str(getattr(tweet, "text", "") or "").strip()
                if not text:
                    continue
                tid = str(getattr(tweet, "id", "") or "")
                if not tid:
                    continue
                url = f"https://x.com/{h}/status/{tid}"
                if url in core_urls:
                    continue
                items_by_url[url] = {
                    "title": f"@{h}: {text[:120]}",
                    "url": url,
                    "summary": text,
                    "source": f"@{h}",
                    "source_type": "twitter_network_discovery",
                    "published": dt.isoformat(),
                    "discovered_via_core": [u for u in evidence.get(h.lower(), []) if u][:5],
                }
                n += 1
            targets.append({
                "handle": h,
                "ok": True,
                "items": n,
                "signal_score": score[h],
                "discovered_via_count": len(evidence.get(h.lower(), [])),
            })
        except Exception as exc:
            targets.append({
                "handle": h,
                "ok": False,
                "signal_score": score[h],
                "error": f"{type(exc).__name__}: {str(exc)[:300]}",
            })
        await asyncio.sleep(2)

    ok = sum(1 for t in targets if t["ok"])
    items = sorted(items_by_url.values(), key=lambda x: x["published"], reverse=True)

    if ok == 0:
        coverage, health = "FAILED", "FAILED"
    elif ok < len(ranked):
        coverage, health = "PARTIAL", "DEGRADED"
    else:
        coverage, health = "COMPLETE", "HEALTHY"

    return {
        **base,
        "coverage": coverage,
        "semantic_health": health,
        "expected_accounts": len(ranked),
        "successful_accounts": ok,
        "targets": targets,
        "items": items,
    }


payload = asyncio.run(collect())
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(
    "X_NETWORK_DISCOVERY",
    payload["coverage"],
    payload["semantic_health"],
    payload["successful_accounts"],
    "/",
    payload["expected_accounts"],
    len(payload["items"]),
)
