#!/usr/bin/env python3
"""Read-only X topic discovery.

This is a discovery layer only. Results are candidates and must be verified
against the original post and, for material claims, an official source.
"""
import asyncio
import json
import os
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import yaml
from dotenv import load_dotenv
from twikit import Client

load_dotenv()

JST = ZoneInfo("Asia/Tokyo")
OUT = Path("cloud-output/x-discovery-latest.json")
OUT.parent.mkdir(parents=True, exist_ok=True)
MAX_PER_QUERY = 20


def tweet_created_at(tweet):
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

    cfg = yaml.safe_load(Path("config/x_discovery.yaml").read_text(encoding="utf-8")) or {}
    queries = cfg.get("queries", [])

    auth = os.getenv("X_AUTH_TOKEN")
    ct0 = os.getenv("X_CT0")
    base = {
        "schema": "ai-daily-news.x-discovery.v1",
        "generated_at": now.isoformat(),
        "window_start": start.isoformat(),
        "window_end": now.isoformat(),
        "write_actions": "NONE",
        "scope": "TOPIC_SEARCH_CANDIDATES_NOT_FULL_X",
        "candidate_only": True,
        "verification_required": True,
        "expected_queries": len(queries),
    }

    if not auth or not ct0:
        return {
            **base,
            "coverage": "FAILED",
            "successful_queries": 0,
            "queries": [],
            "items": [],
            "error": "X read-only secrets are required",
        }

    client = Client("en-US", proxy=os.getenv("PROXY_URL"))
    client.set_cookies({"auth_token": auth, "ct0": ct0})

    query_status = []
    items_by_id = {}

    for qcfg in queries:
        qid = qcfg["id"]
        query = qcfg["query"]
        try:
            tweets = await client.search_tweet(query, "Latest", MAX_PER_QUERY)
            in_window = 0
            for tweet in tweets:
                try:
                    created = tweet_created_at(tweet)
                except Exception:
                    continue
                created_jst = created.astimezone(JST)
                if not (start <= created_jst <= now):
                    continue

                tid = str(getattr(tweet, "id", "") or getattr(tweet, "id_str", ""))
                if not tid:
                    continue
                user = getattr(tweet, "user", None)
                handle = getattr(user, "screen_name", None) or "unknown"
                text = (
                    getattr(tweet, "full_text", None)
                    or getattr(tweet, "text", None)
                    or ""
                ).strip()
                if not text:
                    continue

                in_window += 1
                existing = items_by_id.get(tid)
                if existing:
                    if qid not in existing["matched_queries"]:
                        existing["matched_queries"].append(qid)
                    continue

                items_by_id[tid] = {
                    "tweet_id": tid,
                    "author": f"@{handle}",
                    "title": f"@{handle}: {text[:120]}",
                    "url": f"https://x.com/{handle}/status/{tid}",
                    "summary": text,
                    "source_type": "twitter_discovery",
                    "published": created.isoformat(),
                    "matched_queries": [qid],
                    "metrics": {
                        "likes": int(getattr(tweet, "favorite_count", 0) or 0),
                        "retweets": int(getattr(tweet, "retweet_count", 0) or 0),
                        "replies": int(getattr(tweet, "reply_count", 0) or 0),
                        "views": int(getattr(tweet, "view_count", 0) or 0),
                    },
                }

            query_status.append({
                "id": qid,
                "query": query,
                "ok": True,
                "returned": len(tweets),
                "in_window": in_window,
            })
        except Exception as exc:
            query_status.append({
                "id": qid,
                "query": query,
                "ok": False,
                "error": f"{type(exc).__name__}: {str(exc)[:300]}",
            })
        await asyncio.sleep(2)

    ok = sum(1 for q in query_status if q["ok"])
    coverage = "COMPLETE" if queries and ok == len(queries) else ("FAILED" if ok == 0 else "PARTIAL")
    items = sorted(
        items_by_id.values(),
        key=lambda x: x["published"],
        reverse=True,
    )

    return {
        **base,
        "coverage": coverage,
        "successful_queries": ok,
        "queries": query_status,
        "items": items,
    }


payload = asyncio.run(collect())
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(
    "X_DISCOVERY_EXPORT",
    payload["coverage"],
    payload["successful_queries"],
    "/",
    payload["expected_queries"],
    len(payload["items"]),
)
