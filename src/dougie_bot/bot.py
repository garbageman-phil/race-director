"""Discord client for dougie-bot."""

from __future__ import annotations

import asyncio
import os
import sys
from pathlib import Path

import discord

from race_director.config import load_config
from race_director.formatter import format_results
from race_director.scraper import scrape_race

from dougie_bot.parsing import chunk_discord, extract_race_path, is_help_request, parse_invocation


def _help_text() -> str:
    return (
        "**dougie-bot** — race results from ontheday.net (same plain-text tables as "
        "`python -m race_director --plain`).\n\n"
        "**Examples**\n"
        "- `@dougie-bot what were the race results from 2026/eldo-1-8?`\n"
        "- `dougie-bot, 2026/cbr_4`\n"
        "- `@dougie-bot help`\n\n"
        "**Race path** must match the ontheday.net URL exactly (e.g. `2026/eldo-1-8` or "
        "`2026/cbr_4`), including hyphens vs underscores. "
        "It matches the URL `https://www.ontheday.net/YYYY/event_slug/`.\n\n"
        "Results only include riders whose **team** matches `team_names` in your "
        "`config.yaml` on the machine running the bot. See the repo README and "
        "`DOUGIE_BOT.md` for setup."
    )


def run_bot() -> None:
    token = os.environ.get("DISCORD_TOKEN")
    if not token:
        print("Error: DISCORD_TOKEN is not set.", file=sys.stderr)
        raise SystemExit(1)

    raw_config = os.environ.get("RACE_DIRECTOR_CONFIG")
    config_path = Path(raw_config) if raw_config else None

    intents = discord.Intents.default()
    intents.message_content = True
    client = discord.Client(intents=intents)

    @client.event
    async def on_ready() -> None:
        assert client.user is not None
        print(f"dougie-bot logged in as {client.user} (id={client.user.id})")

    @client.event
    async def on_message(message: discord.Message) -> None:
        if message.author.bot:
            return
        assert client.user is not None
        mentions_bot = client.user in message.mentions
        invoked, body = parse_invocation(message.content, mentions_bot=mentions_bot)
        if not invoked:
            return

        if is_help_request(body):
            for part in chunk_discord(_help_text()):
                await message.reply(part)
            return

        race_path = extract_race_path(body)
        if not race_path:
            await message.reply(
                "I need a race path like `2026/eldo-1-8` or `2026/cbr_4` in your message. "
                "Try `@dougie-bot help`."
            )
            return

        try:
            config = load_config(config_path)
        except SystemExit:
            await message.reply(
                "Configuration error: could not load `config.yaml`. "
                "Set `RACE_DIRECTOR_CONFIG` to its path if it is not in the "
                "process working directory."
            )
            return

        team_lower = config.team_names_lower()
        async with message.channel.typing():
            try:
                outcome = await asyncio.to_thread(scrape_race, race_path, team_lower)
            except RuntimeError as exc:
                await message.reply(f"Error fetching results: {exc}")
                return

        if not outcome.finish and not outcome.primes and not outcome.mar:
            await message.reply("No results found for the configured team names.")
            return

        text = format_results(outcome, markdown=False)
        for part in chunk_discord(text):
            await message.reply(part)

    client.run(token)
