"""Local markdown file publisher — always-on default."""

import os

NAME = "markdown"


def is_configured():
    return True


def publish(digest_md, date_str, audio_path=None, filtered_info=None, output_dir="data", **_):
    os.makedirs(output_dir, exist_ok=True)
    path = os.path.join(output_dir, f"digest-{date_str}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(digest_md)
    return path
