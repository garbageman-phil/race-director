"""Tests for dougie_bot parsing helpers (no Discord, no network)."""

from __future__ import annotations

from dougie_bot.parsing import (
    chunk_discord,
    extract_race_path,
    is_help_request,
    parse_invocation,
)


def test_parse_invocation_mention() -> None:
    invoked, body = parse_invocation("<@123> 2026/cbr_4 please", mentions_bot=True)
    assert invoked is True
    assert body == "2026/cbr_4 please"


def test_parse_invocation_prefix() -> None:
    invoked, body = parse_invocation("dougie-bot, what about 2026/foo_bar?", mentions_bot=False)
    assert invoked is True
    assert "2026/foo_bar" in body


def test_parse_invocation_not_invoked() -> None:
    invoked, _ = parse_invocation("hello world", mentions_bot=False)
    assert invoked is False


def test_extract_race_path() -> None:
    assert extract_race_path("results from 2026/cbr_4 thanks") == "2026/cbr_4"
    assert extract_race_path("results from 2026/eldo-1-8 thanks") == "2026/eldo-1-8"
    assert extract_race_path("no path here") is None


def test_is_help_request() -> None:
    assert is_help_request("") is True
    assert is_help_request("help") is True
    assert is_help_request("HELP ME") is True
    assert is_help_request("?") is True
    assert is_help_request("2026/cbr_4") is False


def test_chunk_discord_short() -> None:
    assert chunk_discord("hello") == ["hello"]
    assert chunk_discord("") == []


def test_chunk_discord_splits_long_line() -> None:
    s = "a" * 5000
    parts = chunk_discord(s, limit=1990)
    assert len(parts) > 1
    assert all(len(p) <= 1990 for p in parts)
    assert "".join(parts) == s
