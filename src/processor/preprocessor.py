"""Preprocessing pipeline: score → dedup → classify → sort."""

import math
from datetime import datetime, timezone
from difflib import SequenceMatcher


def _parse_time(published_str):
    """Parse ISO format time string, return datetime or None."""
    if not published_str:
        return None
    try:
        return datetime.fromisoformat(published_str)
    except (ValueError, TypeError):
        return None


def _time_decay(published_str, half_life_hours=24):
    """Exponential decay based on age. Returns 0~1."""
    dt = _parse_time(published_str)
    if not dt:
        return 0.5  # unknown age gets middle value
    now = datetime.now(timezone.utc)
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    age_hours = max((now - dt).total_seconds() / 3600, 0)
    return math.pow(0.5, age_hours / half_life_hours)


def _safe_log2(n):
    """log2 that handles 0 and negative values."""
    return math.log2(n + 1) if n and n > 0 else 0


def _build_weight_map(accounts_config):
    """Build handle -> weight multiplier map from accounts config."""
    weight_map = {}
    for acc in accounts_config.get("accounts", []):
        handle = acc.get("handle", "")
        w = acc.get("weight", "medium")
        weight_map[handle.lower()] = 3 if w == "high" else 1
    return weight_map


def score_items(items, accounts_config):
    """Score each item based on engagement, account weight, and recency."""
    weight_map = _build_weight_map(accounts_config)

    for item in items:
        decay = _time_decay(item.get("published"))

        if item.get("source_type") == "twitter":
            metrics = item.get("metrics", {})
            likes = _safe_log2(metrics.get("likes", 0))
            retweets = _safe_log2(metrics.get("retweets", 0))
            replies = _safe_log2(metrics.get("replies", 0))
            engagement = likes * 3 + retweets * 4 + replies * 2

            handle = item.get("source", "").lstrip("@").lower()
            account_weight = weight_map.get(handle, 1)

            item["score"] = round(engagement * account_weight * decay, 2)
        else:
            # RSS: fixed base score * decay
            item["score"] = round(15 * decay, 2)

    return items


def _similarity(a, b):
    """String similarity ratio using SequenceMatcher."""
    if not a or not b:
        return 0.0
    return SequenceMatcher(None, a.lower(), b.lower()).ratio()


def dedup(items):
    """Three-layer dedup: URL → title similarity → summary similarity."""
    kept = []
    seen_urls = set()

    for item in items:
        url = item.get("url", "")
        merged = False

        # Layer 1: exact URL match
        if url and url in seen_urls:
            for k in kept:
                if k.get("url") == url:
                    k.setdefault("related_sources", []).append({
                        "source": item.get("source"),
                        "url": url,
                    })
                    if item.get("score", 0) > k.get("score", 0):
                        k["score"] = item["score"]
                    merged = True
                    break
            if merged:
                continue

        # Layer 2: title similarity >= 0.65
        title = item.get("title", "")
        for k in kept:
            if _similarity(title, k.get("title", "")) >= 0.65:
                k.setdefault("related_sources", []).append({
                    "source": item.get("source"),
                    "url": item.get("url"),
                })
                if item.get("score", 0) > k.get("score", 0):
                    k["score"] = item["score"]
                    k["title"] = title
                    k["summary"] = item.get("summary", k.get("summary", ""))
                    k["url"] = item.get("url", k.get("url", ""))
                merged = True
                break
            if merged:
                break
        if merged:
            continue

        # Layer 3: Twitter summary similarity >= 0.8
        if item.get("source_type") == "twitter":
            summary = item.get("summary", "")
            for k in kept:
                if k.get("source_type") == "twitter" and _similarity(summary, k.get("summary", "")) >= 0.8:
                    k.setdefault("related_sources", []).append({
                        "source": item.get("source"),
                        "url": item.get("url"),
                    })
                    if item.get("score", 0) > k.get("score", 0):
                        k["score"] = item["score"]
                        k["title"] = title
                        k["summary"] = summary
                        k["url"] = item.get("url", k.get("url", ""))
                    merged = True
                    break
        if merged:
            continue

        # No match — keep as new item
        if url:
            seen_urls.add(url)
        kept.append(item)

    return kept


CATEGORY_KEYWORDS = {
    "要闻": [
        "发布", "launch", "release", "announce", "open source", "开源",
        "收购", "acqui", "merger", "融资", "funding", "billion", "million",
        "ban", "regulation", "监管", "政策", "policy",
    ],
    "产品": [
        "update", "更新", "feature", "功能", "app", "tool", "plugin",
        "api", "sdk", "model", "版本", "beta", "alpha", "v1", "v2",
    ],
    "观点": [
        "think", "believe", "opinion", "观点", "看法", "predict", "预测",
        "thread", "take", "hot take", "rant", "essay", "反思",
    ],
}


def classify_items(items):
    """Keyword-based pre-classification as suggestion for LLM."""
    for item in items:
        text = f"{item.get('title', '')} {item.get('summary', '')}".lower()
        matched = "其他"
        for category, keywords in CATEGORY_KEYWORDS.items():
            if any(kw in text for kw in keywords):
                matched = category
                break
        item["suggested_category"] = matched
    return items


def preprocess(items, accounts_config):
    """Full preprocessing pipeline: score → dedup → classify → sort."""
    original_count = len(items)

    items = score_items(items, accounts_config)
    items = dedup(items)
    items = classify_items(items)
    items.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Add source_count for multi-source items
    for item in items:
        related = item.get("related_sources", [])
        item["source_count"] = 1 + len(related)

    dedup_count = original_count - len(items)

    # Light filtering: remove very low score items (noise)
    before_filter = len(items)
    items = [i for i in items if i.get("score", 0) >= 5]
    filtered_count = before_filter - len(items)

    return items, {
        "original": original_count,
        "after_dedup": before_filter,
        "removed": dedup_count,
        "after_filter": len(items),
        "filtered": filtered_count,
    }
