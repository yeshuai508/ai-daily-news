"""Publishers convert a digest into a delivered output.

Each publisher module exposes:
    - NAME: short identifier
    - is_configured() -> bool: whether required env vars are set
    - publish(digest_md, date_str, **kwargs) -> str: deliver and return a result string
"""

from . import wechat, telegram, markdown_file

ALL_PUBLISHERS = [markdown_file, wechat, telegram]


def active_publishers(names=None):
    """Return publishers that are configured. If `names` given, restrict to those."""
    publishers = ALL_PUBLISHERS
    if names:
        wanted = set(names)
        publishers = [p for p in publishers if p.NAME in wanted]
    return [p for p in publishers if p.is_configured()]
