#!/usr/bin/env python3
"""Authenticated, read-only X search fallback using a cloud browser.

Used only when the internal SearchTimeline client returns an empty/suspect
candidate set. It performs no account write actions.
"""
import asyncio
import json
import os
import re
import shutil
from datetime import datetime, timedelta, timezone
from pathlib import Path
from urllib.parse import quote
from zoneinfo import ZoneInfo

import yaml
from playwright.async_api import async_playwright, TimeoutError as PlaywrightTimeoutError

JST = ZoneInfo("Asia/Tokyo")
OUT = Path("cloud-output/x-discovery-latest.json")
OUT.parent.mkdir(parents=True, exist_ok=True)
MAX_PER_QUERY = 12


def iso_to_dt(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except Exception:
        return None


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
        "collector_method": "authenticated_browser_search_fallback",
        "expected_queries": len(queries),
    }
    if not auth or not ct0:
        return {**base, "coverage": "FAILED", "semantic_health": "FAILED",
                "successful_queries": 0, "queries": [], "items": [],
                "error": "X read-only secrets are required"}

    chrome = (
        shutil.which("google-chrome")
        or shutil.which("google-chrome-stable")
        or shutil.which("chromium")
        or shutil.which("chromium-browser")
    )
    if not chrome:
        return {**base, "coverage": "FAILED", "semantic_health": "FAILED",
                "successful_queries": 0, "queries": [], "items": [],
                "error": "No system Chrome/Chromium found on runner"}

    statuses = []
    items_by_id = {}

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            executable_path=chrome,
            headless=True,
            args=["--no-sandbox", "--disable-dev-shm-usage"],
        )
        context = await browser.new_context(
            locale="en-US",
            viewport={"width": 1365, "height": 900},
            user_agent=(
                "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                "(KHTML, like Gecko) Chrome/153.0.0.0 Safari/537.36"
            ),
        )
        await context.add_cookies([
            {"name": "auth_token", "value": auth, "domain": ".x.com", "path": "/", "secure": True},
            {"name": "ct0", "value": ct0, "domain": ".x.com", "path": "/", "secure": True},
        ])
        page = await context.new_page()

        for qcfg in queries:
            qid = qcfg["id"]
            query = qcfg["query"]
            url = f"https://x.com/search?q={quote(query)}&src=typed_query&f=live"
            try:
                response = await page.goto(url, wait_until="domcontentloaded", timeout=30000)
                status_code = response.status if response else None
                try:
                    await page.wait_for_selector('article[data-testid="tweet"]', timeout=15000)
                except PlaywrightTimeoutError:
                    pass

                # Scroll once to catch a second small batch without turning this into a crawler.
                await page.mouse.wheel(0, 1600)
                await page.wait_for_timeout(1500)

                articles = page.locator('article[data-testid="tweet"]')
                count = min(await articles.count(), MAX_PER_QUERY)
                in_window = 0
                parsed = 0

                for idx in range(count):
                    article = articles.nth(idx)
                    status_links = article.locator('a[href*="/status/"]')
                    href = None
                    for j in range(min(await status_links.count(), 8)):
                        candidate = await status_links.nth(j).get_attribute("href")
                        if candidate and re.search(r"/status/\d+", candidate):
                            href = candidate
                            break
                    if not href:
                        continue
                    m = re.search(r"^/([^/]+)/status/(\d+)", href)
                    if not m:
                        continue
                    handle, tid = m.group(1), m.group(2)

                    text_node = article.locator('[data-testid="tweetText"]')
                    text = ""
                    if await text_node.count():
                        try:
                            text = (await text_node.first.inner_text()).strip()
                        except Exception:
                            text = ""
                    if not text:
                        continue

                    time_node = article.locator("time")
                    published = None
                    if await time_node.count():
                        published = iso_to_dt(await time_node.first.get_attribute("datetime"))
                    if not published:
                        continue
                    published_jst = published.astimezone(JST)
                    parsed += 1
                    if not (start <= published_jst <= now):
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
                        "published": published.isoformat(),
                        "matched_queries": [qid],
                    }

                statuses.append({
                    "id": qid,
                    "query": query,
                    "ok": status_code == 200,
                    "http_status": status_code,
                    "visible_tweets": count,
                    "parsed": parsed,
                    "in_window": in_window,
                })
            except Exception as exc:
                statuses.append({
                    "id": qid,
                    "query": query,
                    "ok": False,
                    "error": f"{type(exc).__name__}: {str(exc)[:300]}",
                })
            await page.wait_for_timeout(1200)

        await browser.close()

    ok = sum(1 for q in statuses if q.get("ok"))
    visible = sum(q.get("visible_tweets", 0) for q in statuses)
    in_window = sum(q.get("in_window", 0) for q in statuses)

    if ok == 0:
        coverage, semantic_health = "FAILED", "FAILED"
    elif visible == 0:
        coverage, semantic_health = "EMPTY", "SUSPECT_EMPTY"
    elif ok < len(queries):
        coverage, semantic_health = "PARTIAL", "DEGRADED"
    else:
        coverage, semantic_health = "COMPLETE", "HEALTHY"

    items = sorted(items_by_id.values(), key=lambda x: x["published"], reverse=True)
    return {
        **base,
        "coverage": coverage,
        "semantic_health": semantic_health,
        "successful_queries": ok,
        "total_visible_tweets": visible,
        "total_in_window": in_window,
        "queries": statuses,
        "items": items,
    }


payload = asyncio.run(collect())
OUT.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
print(
    "X_BROWSER_DISCOVERY",
    payload["coverage"],
    payload["semantic_health"],
    payload.get("successful_queries", 0),
    "/",
    payload["expected_queries"],
    payload.get("total_visible_tweets", 0),
    payload.get("total_in_window", 0),
    len(payload["items"]),
)
