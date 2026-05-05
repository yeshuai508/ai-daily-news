"""Telegram channel publisher.

Set TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID to enable.
Long digests are split across multiple messages (Telegram caps at 4096 chars).
"""

import os
import requests

NAME = "telegram"

API = "https://api.telegram.org"
MAX_LEN = 4000  # leave headroom under 4096 limit


def is_configured():
    return bool(os.getenv("TELEGRAM_BOT_TOKEN") and os.getenv("TELEGRAM_CHAT_ID"))


def _split(text, limit=MAX_LEN):
    chunks = []
    while len(text) > limit:
        cut = text.rfind("\n\n", 0, limit)
        if cut < limit // 2:
            cut = text.rfind("\n", 0, limit)
        if cut < limit // 2:
            cut = limit
        chunks.append(text[:cut])
        text = text[cut:].lstrip()
    if text:
        chunks.append(text)
    return chunks


def publish(digest_md, date_str, audio_path=None, **_):
    token = os.environ["TELEGRAM_BOT_TOKEN"]
    chat_id = os.environ["TELEGRAM_CHAT_ID"]
    base = f"{API}/bot{token}"

    last_id = None
    for chunk in _split(digest_md):
        resp = requests.post(
            f"{base}/sendMessage",
            json={"chat_id": chat_id, "text": chunk, "parse_mode": "Markdown", "disable_web_page_preview": True},
            timeout=15,
        )
        data = resp.json()
        if not data.get("ok"):
            raise RuntimeError(f"Telegram sendMessage failed: {data}")
        last_id = data["result"]["message_id"]

    if audio_path and os.path.isfile(audio_path):
        with open(audio_path, "rb") as f:
            resp = requests.post(
                f"{base}/sendAudio",
                data={"chat_id": chat_id, "title": f"AI Daily {date_str}"},
                files={"audio": f},
                timeout=120,
            )
        if not resp.json().get("ok"):
            raise RuntimeError(f"Telegram sendAudio failed: {resp.json()}")

    return f"telegram:{chat_id}:{last_id}"
