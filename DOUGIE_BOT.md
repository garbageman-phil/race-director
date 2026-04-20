# dougie-bot (Discord)

**dougie-bot** is a Discord bot that answers questions about cycling race results by running the same logic as the race-director CLI with plain-text output (`python -m race_director --plain --race-path …`). Use it in team channels such as **SDBC Racing Team** so members can query ontheday.net results without running Python locally.

## Prerequisites

- A [Discord](https://discord.com) account and permission to add bots to your server (e.g. the **SDBC Racing Team** server).
- Python 3.10+, git, and network access to `ontheday.net` from the machine that runs the bot.

## 1. Create the Discord application and bot

In the [Discord Developer Portal](https://discord.com/developers/applications):

1. **New Application** — choose any application name.
2. Open **Bot** → **Add Bot** → set the bot **username** to **dougie-bot** (or your preferred display name).
3. Under **Bot**, enable **Privileged Gateway Intents** → **Message Content Intent** (required so the bot can read message text and detect mentions and commands).
4. **Reset Token**, copy it once, and store it only in environment variables or a local secret manager — **never commit the token** to git.
5. **OAuth2 → URL Generator**: select scope **bot**. For **Bot Permissions**, enable at least **Send Messages**, **Read Messages/View Channels**, and **Read Message History**. Open the generated URL in a browser to **invite the bot** into the **SDBC Racing Team** server (or your test server first).

## 2. Install race-director with Discord support

On the host that will run the bot:

```bash
git clone <your-repo-url> && cd race-director
python3 -m venv .venv
source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -e ".[discord]"
```

## 3. Configuration (`config.yaml`)

The bot uses the same `config.yaml` as the CLI: copy `config.example.yaml` to `config.yaml` and set `team_names` to every spelling your timing company might use for your team (e.g. SDBC variants).

```bash
cp config.example.yaml config.yaml
# edit config.yaml
```

`config.yaml` is gitignored. The bot looks for it in the **process working directory** unless you set `RACE_DIRECTOR_CONFIG` (see below).

## 4. Environment variables

| Variable | Required | Description |
|----------|----------|-------------|
| `DISCORD_TOKEN` | Yes | Bot token from the Developer Portal. |
| `RACE_DIRECTOR_CONFIG` | No | Absolute or relative path to `config.yaml` if it is not in the current working directory. |

Optional: load these from a `.env` file with a shell or process manager (keep `.env` out of git).

## 5. Run the bot

From the directory that contains `config.yaml` (or with `RACE_DIRECTOR_CONFIG` set):

```bash
export DISCORD_TOKEN='your-bot-token'
python -m dougie_bot
```

Alternatively, after install, the `dougie-bot` console script points at the same entry point:

```bash
dougie-bot
```

Leave the process running (tmux, systemd, Docker, or a small PaaS). The bot only responds where it can read messages and send replies (the channels granted by your invite and server permissions).

## 6. Using dougie-bot in Discord

- **Mention** the bot and include a **race path** in the form `YYYY/event_slug` (e.g. `2026/cbr_4`), matching the ontheday.net URL path.
  - Example: `@dougie-bot what were the race results from 2026/cbr_4?`
- Or start a message with **`dougie-bot,`** (case-insensitive) and the path in the same message.
  - Example: `dougie-bot, 2026/cbr_4`
- **Help**: `@dougie-bot help` or `dougie-bot, help`

The bot replies with plain-text tables (and splits long output into multiple messages under Discord’s length limit).

## 7. SDBC Racing Team

Invite **dougie-bot** into the **SDBC Racing Team** Discord server using the OAuth URL from the Portal. Grant it access to the text channels where you want results queries (e.g. a `#race-results` or general team channel). If you need the bot to respond only in specific channels later, restrict those channels in Discord’s channel permissions for the bot role, or extend the bot code with an allowlist (not included by default).

## 8. Troubleshooting

| Issue | What to check |
|-------|----------------|
| Bot is offline | Token correct? Process running? Network up? |
| Bot does not reply | **Message Content Intent** enabled on the Bot page? Bot has Send/Read permissions in that channel? |
| “Configuration error” / config | `config.yaml` exists on the host; or set `RACE_DIRECTOR_CONFIG` to its full path. |
| “No results found” | `team_names` in `config.yaml` must match team strings on the timing sheets (case-insensitive). |
| Fetch errors | Race path must match the site (e.g. `2026/cbr_4`); check ontheday.net in a browser. |

## 9. Manual smoke test (CLI)

To verify scraping without Discord:

```bash
python -m race_director --plain --race-path 2026/cbr_4
```

Use `--quiet` to skip the configured team list on stdout. See the main [README](README.md) for full CLI options.
