"""Read-only X collector using twikit.

Two independent layers:
1) fixed account watchlist: deterministic must-check coverage;
2) keyword discovery: broader, non-exhaustive discovery outside the watchlist.

"COMPLETE" applies only to the fixed watchlist. Discovery health is reported
separately and must never be described as complete coverage of X.
"""
import asyncio
import os
import yaml
from datetime import datetime, timedelta, timezone

from dotenv import load_dotenv
from twikit import Client

load_dotenv()

MAX_TWEETS_PER_ACCOUNT = 40
MAX_TWEETS_PER_QUERY = 30
DISCOVERY_CONFIG = "config/x_discovery_queries.yaml"


def _parse_created_at(value):
    if not value:
        return None
    if isinstance(value, datetime):
        return value if value.tzinfo else value.replace(tzinfo=timezone.utc)
    for fmt in ("%a %b %d %H:%M:%S %z %Y",):
        try:
            return datetime.strptime(str(value), fmt)
        except ValueError:
            pass
    try:
        parsed = datetime.fromisoformat(str(value))
        return parsed if parsed.tzinfo else parsed.replace(tzinfo=timezone.utc)
    except ValueError:
        return None


def _tweet_text(tweet):
    return (
        getattr(tweet, "full_text", None)
        or getattr(tweet, "text", None)
        or ""
    )


def _tweet_handle(tweet, fallback=None):
    user = getattr(tweet, "user", None)
    handle = getattr(user, "screen_name", None) if user else None
    return handle or fallback or "unknown"


def _tweet_to_item(tweet, handle=None, source_type="twitter", discovery_query=None):
    created = _parse_created_at(getattr(tweet, "created_at", None))
    h = _tweet_handle(tweet, handle)
    text = _tweet_text(tweet)
    tweet_id = str(getattr(tweet, "id", None) or getattr(tweet, "id_str", ""))
    item = {
        "title": f"@{h}: {text[:80]}",
        "url": f"https://x.com/{h}/status/{tweet_id}" if tweet_id else "",
        "summary": text,
        "source": f"@{h}",
        "source_type": source_type,
        "published": created.isoformat() if created else None,
        "metrics": {
            "likes": getattr(tweet, "favorite_count", 0) or 0,
            "retweets": getattr(tweet, "retweet_count", 0) or 0,
            "replies": getattr(tweet, "reply_count", 0) or 0,
            "views": getattr(tweet, "view_count", 0) or 0,
        },
    }
    if discovery_query:
        item["discovery_query"] = discovery_query
    return item, created


def _load_yaml(path):
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


async def _collect_watchlist(client, cutoff):
    config = _load_yaml("config/x_accounts.yaml")
    items = []
    targets = []

    for account in config.get("accounts", []):
        handle = account["handle"]
        try:
            user = await client.get_user_by_screen_name(handle)
            tweets = await user.get_tweets("Tweets", count=MAX_TWEETS_PER_ACCOUNT)
            count = 0
            for tweet in tweets:
                item, created = _tweet_to_item(tweet, handle=handle)
                if not created or created < cutoff:
                    continue
                items.append(item)
                count += 1
            targets.append({"handle": handle, "ok": True, "items": count})
        except Exception as exc:
            targets.append(
                {"handle": handle, "ok": False, "error": str(exc)[:300]}
            )
        await asyncio.sleep(2)

    successful = sum(1 for target in targets if target["ok"])
    expected = len(targets)
    coverage = (
        "COMPLETE"
        if expected and successful == expected
        else ("FAILED" if successful == 0 else "PARTIAL")
    )
    return {
        "coverage": coverage,
        "expected_accounts": expected,
        "successful_accounts": successful,
        "targets": targets,
        "items": items,
    }


async def _collect_discovery(client, cutoff):
    if not os.path.exists(DISCOVERY_CONFIG):
        return {
            "coverage": "NOT_CONFIGURED",
            "expected_queries": 0,
            "successful_queries": 0,
            "queries": [],
            "items": [],
            "scope_note": "No discovery query config present.",
        }

    config = _load_yaml(DISCOVERY_CONFIG)
    items = []
    query_results = []
    seen_urls = set()

    for entry in config.get("queries", []):
        query_id = entry.get("id") or "unnamed"
        query = (entry.get("query") or "").strip()
        if not query:
            query_results.append(
                {"id": query_id, "ok": False, "items": 0, "error": "empty query"}
            )
            continue
        try:
            tweets = await client.search_tweet(query, "Latest", MAX_TWEETS_PER_QUERY)
            count = 0
            for tweet in tweets:
                item, created = _tweet_to_item(
                    tweet,
                    source_type="twitter_discovery",
                    discovery_query=query_id,
                )
                if not created or created < cutoff:
                    continue
                url = item.get("url")
                if url and url in seen_urls:
                    continue
                if url:
                    seen_urls.add(url)
                items.append(item)
                count += 1
            query_results.append({"id": query_id, "ok": True, "items": count})
        except Exception as exc:
            query_results.append(
                {"id": query_id, "ok": False, "items": 0, "error": str(exc)[:300]}
            )
        await asyncio.sleep(2)

    expected = len(query_results)
    successful = sum(1 for result in query_results if result["ok"])
    coverage = (
        "COMPLETE"
        if expected and successful == expected
        else ("FAILED" if successful == 0 else "PARTIAL")
    )

    return {
        "coverage": coverage,
        "expected_queries": expected,
        "successful_queries": successful,
        "queries": query_results,
        "items": items,
        "scope_note": (
            "Discovery searches X by configured high-signal queries. "
            "It broadens discovery beyond the fixed watchlist but does not "
            "guarantee exhaustive X coverage, pagination completeness, replies, "
            "long posts, protected posts, or every repost/quote."
        ),
    }


async def _collect_report(hours=40):
    auth = os.getenv("X_AUTH_TOKEN")
    ct0 = os.getenv("X_CT0")
    if not auth or not ct0:
        raise RuntimeError("X read-only secrets are required")

    client = Client("en-US", proxy=os.getenv("PROXY_URL"))
    client.set_cookies({"auth_token": auth, "ct0": ct0})
    cutoff = datetime.now(timezone.utc) - timedelta(hours=hours)

    watchlist = await _collect_watchlist(client, cutoff)
    discovery = await _collect_discovery(client, cutoff)

    combined = []
    seen_urls = set()
    for item in watchlist["items"] + discovery["items"]:
        url = item.get("url")
        if url and url in seen_urls:
            continue
        if url:
            seen_urls.add(url)
        combined.append(item)

    return {
        # Backward-compatible fixed-watchlist health fields.
        "coverage": watchlist["coverage"],
        "expected_accounts": watchlist["expected_accounts"],
        "successful_accounts": watchlist["successful_accounts"],
        "targets": watchlist["targets"],
        # New explicit semantics.
        "coverage_scope": "FIXED_WATCHLIST_ONLY",
        "watchlist": {
            key: value for key, value in watchlist.items() if key != "items"
        },
        "discovery": {
            key: value for key, value in discovery.items() if key != "items"
        },
        "items": combined,
    }


def collect_twitter_report(hours=40):
    return asyncio.run(_collect_report(hours))


def collect_twitter(hours=24):
    return collect_twitter_report(hours)["items"]
