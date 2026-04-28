# race-director

As a race director for a cycling team, it may be important to you to collect all your team member's race results given that there may be a lot of team racers participating in many events over a weekend.  This app strives to collect all the information and present it in a markdown or plain text table.

A Python CLI tool that scrapes cycling race results from [ontheday.net](https://www.ontheday.net) and filters them by team name. Point it at any race event — multi-stage or single-day — and get a clean table of your team's finishes across every category. When the timing pages include **Primes** or **Most Assertive Rider (MAR)** tables, matching team rows are listed in additional sections after the main finish table (same team-name rules as finishes).

## Prerequisites

- Python 3.10+
- Network access to `ontheday.net`

## Installation

```bash
git clone <repo-url> && cd race-director
git pull # to get all the latest updates
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
```

## Configuration

Copy the example config and edit it with your team's name variants:

```bash
cp config.example.yaml config.yaml
```

`config.yaml` must contain a `team_names` list. Matching is case-insensitive, so include every spelling the timing company might use:

```yaml
team_names:
  - "SDBC"
  - "San Diego Bicycle Club powered by Bonnici Law Group"
  - "San Diego Bicycle Club"
```

The file is gitignored. See `config.example.yaml` for the committed template.

## Usage

```bash
# Default: Markdown table (GitHub-Flavored Markdown, ready to paste into a PR or doc)
python -m race_director

# Plain-text table
python -m race_director --plain

# Non-interactive: pass the race path on the command line (no prompt)
python -m race_director --plain --race-path 2026/murrieta

# Same, but skip printing the configured team names (useful for scripts)
python -m race_director --plain --race-path 2026/murrieta --quiet

# Use a config file outside the current directory
python -m race_director --config /path/to/config.yaml --race-path 2026/murrieta
```

**Interactive mode:** if you omit `--race-path`, the tool prints your configured team names and prompts for a race path:

```
Enter race path (e.g. 2026/murrieta): 2026/murrieta
```

The race path corresponds to the URL on ontheday.net — for `https://www.ontheday.net/2026/murrieta/`, enter `2026/murrieta`. Both multi-stage events and single-day races (e.g. `2026/cbr_2`) are supported.

Default output is a GitHub-Flavored Markdown table, ready to paste into a PR or doc:

```markdown
## Race Results

| Race Name                                    | Rider Name  | Rider Place |
|----------------------------------------------|-------------|-------------|
| Stage 1 - Grand Prix (Open 2/3)              | Bart | 29th        |
| Stage 2 - Circuit Race (Open 4/5)            | Lisa | 4th         |

**2 result(s) found.**
```

With `--plain`, output is a plain-text table:

```
Race Name                                     Rider Name        Rider Place
--------------------------------------------  ----------------  -------------
Stage 1 - Grand Prix (Open 2/3)               Bart       29th
Stage 1 - Grand Prix (Masters 45+ 1/2/3/4)    Homer           15th
Stage 2 - Circuit Race (Open 4/5)             Marge       4th
...
```

For single-day races the Race Name column shows just the category:

```
Race Name              Rider Name        Rider Place
---------------------  ----------------  -------------
Masters 50+ (Cat 1-4)  Mr Burns    7th
Masters 40+ (Cat 1-3)  Homer           19th
...
```

Primes and MAR use the same `team_names` matching as finishes. Example Markdown output shape:

```markdown
### Primes

| Race Name             | Rider Name | Prime      | Points |
|-----------------------|------------|------------|--------|
| Masters 50+ (Cat 1-4) | Lisa   | Men 50+ #1 | 10     |

**1 prime result(s).**

### Most Assertive Rider (MAR)

| Race Name                                        | Rider Name | Place | Points |
|--------------------------------------------------|------------|-------|--------|
| Most Assertive Rider (MAR) – Masters 50+ 1/2/3/4 | Lisa   | = 2   | 3      |

**1 MAR result(s).**
```

## Quickstart

1. Clone the repo and create a virtualenv:
   ```bash
   python3 -m venv .venv && source .venv/bin/activate
   ```
2. Install:
   ```bash
   pip install -e .
   ```
3. Create your config:
   ```bash
   cp config.example.yaml config.yaml
   ```
4. Run:
   ```bash
   python -m race_director
   ```
5. Enter a race path when prompted (e.g. `2026/murrieta`), or pass `--race-path` for non-interactive runs.

## Discord bot (dougie-bot)

To run **dougie-bot** in a Discord server (e.g. **SDBC Racing Team**), install optional dependencies (`pip install -e ".[discord]"`), set `DISCORD_TOKEN`, and follow [DOUGIE_BOT.md](DOUGIE_BOT.md).

## License

Apache 2.0 — see [LICENSE](LICENSE).
