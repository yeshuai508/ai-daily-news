"""Sensitive content filter for China mainland compliance."""

import os
import re
import yaml


def _load_sensitive_words():
    """Load sensitive words from config/sensitive_words.yaml."""
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        "config",
        "sensitive_words.yaml",
    )
    with open(config_path, encoding="utf-8") as f:
        data = yaml.safe_load(f)

    words = []
    for category in data.values():
        if isinstance(category, list):
            words.extend(category)
    return words


def check_content(text):
    """Check text for sensitive content.

    Returns:
        (is_safe, flagged_terms): bool and list of matched terms.
    """
    words = _load_sensitive_words()
    flagged = [w for w in words if w in text]
    return (len(flagged) == 0, flagged)


def filter_content(text):
    """Remove lines/bullet points containing sensitive words.

    Strategy:
    - Split by lines, remove any line containing a sensitive word.
    - If a section heading (##/###) has no content after it, remove the heading too.
    """
    words = _load_sensitive_words()
    lines = text.split("\n")
    filtered = []

    for line in lines:
        if any(w in line for w in words):
            continue
        filtered.append(line)

    # Remove empty section headings (heading followed by another heading or EOF)
    result = []
    for i, line in enumerate(filtered):
        if re.match(r'^#{2,}\s+', line):
            # Look ahead: is there any non-empty, non-heading content before next heading/EOF?
            has_content = False
            for j in range(i + 1, len(filtered)):
                next_line = filtered[j].strip()
                if re.match(r'^#{2,}\s+', filtered[j]):
                    break
                if next_line:
                    has_content = True
                    break
            if not has_content:
                continue
        result.append(line)

    return "\n".join(result)
