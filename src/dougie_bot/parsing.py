"""Message parsing helpers (no Discord imports)."""

from __future__ import annotations

import re

_RACE_PATH_PATTERN = re.compile(r"\b(20\d{2}/[a-z0-9_]+)\b", re.IGNORECASE)
_MENTION_PREFIX_RE = re.compile(r"^<@!?\d+>\s*")
_BOT_PREFIX = "dougie-bot"


def parse_invocation(content: str, *, mentions_bot: bool) -> tuple[bool, str]:
    """Return whether the bot was invoked and the message body after the trigger."""
    text = content.strip()
    if mentions_bot:
        body = _MENTION_PREFIX_RE.sub("", text, count=1).strip()
        return True, body
    lower = text.lower()
    if lower.startswith(_BOT_PREFIX.lower()):
        rest = text[len(_BOT_PREFIX) :].lstrip(" \t,:").strip()
        return True, rest
    return False, ""


def extract_race_path(text: str) -> str | None:
    m = _RACE_PATH_PATTERN.search(text)
    return m.group(1) if m else None


def is_help_request(body: str) -> bool:
    b = body.strip().lower()
    if not b:
        return True
    words = b.split()
    if not words:
        return True
    return words[0] in ("help", "?", "h")


def chunk_discord(text: str, limit: int = 1990) -> list[str]:
    """Split text into chunks under Discord's message length limit."""
    if not text:
        return []
    if len(text) <= limit:
        return [text]
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(start + limit, len(text))
        if end < len(text):
            window = text[start:end]
            nl = window.rfind("\n")
            if nl > limit // 2:
                end = start + nl + 1
        chunks.append(text[start:end])
        start = end
    return chunks
