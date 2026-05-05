"""Generate daily digest using LLM."""

import os
import json
from openai import OpenAI


def _load_prompt():
    """Load system prompt based on DIGEST_LANG (default zh)."""
    lang = os.getenv("DIGEST_LANG", "zh")
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    path = os.path.join(root, "prompts", f"digest_{lang}.md")
    if not os.path.isfile(path):
        path = os.path.join(root, "prompts", "digest_zh.md")
    with open(path, encoding="utf-8") as f:
        return f.read()


def generate_digest(items: list[dict], date_str: str) -> str:
    client = OpenAI(
        api_key=os.getenv("LLM_API_KEY"),
        base_url=os.getenv("LLM_BASE_URL", "https://api.moonshot.cn/v1"),
    )

    items_text = json.dumps(items, ensure_ascii=False, indent=2)
    user_prompt_zh = f"以下是{date_str}采集到的AI相关信息，请整理成日报：\n\n{items_text}"
    user_prompt_en = f"Raw items collected for {date_str}. Build the digest:\n\n{items_text}"
    user_prompt = user_prompt_en if os.getenv("DIGEST_LANG", "zh") == "en" else user_prompt_zh

    response = client.chat.completions.create(
        model=os.getenv("LLM_MODEL", "moonshot-v1-32k"),
        max_tokens=8192,
        temperature=0.3,
        messages=[
            {"role": "system", "content": _load_prompt()},
            {"role": "user", "content": user_prompt},
        ],
    )

    return response.choices[0].message.content
