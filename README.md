# race-director

A Python CLI tool that scrapes cycling race results from [ontheday.net](https://www.ontheday.net) and filters them by team name. Point it at any race event and get a clean table of your team's finishes across every stage and category.

## Prerequisites

- Python 3.10+
- Network access to `ontheday.net`

## Installation

```bash
git clone <repo-url> && cd race-director
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
python -m race_director
```

The tool will display your configured team names and prompt for a race path:

```
Enter race path (e.g. 2026/murrieta): 2026/murrieta
```

The race path corresponds to the URL on ontheday.net — for `https://www.ontheday.net/2026/murrieta/`, enter `2026/murrieta`.

Output is a table of all your team's results across every stage and category:

```
Race Name                                     Rider Name        Rider Place
--------------------------------------------  ----------------  -------------
Stage 1 - Grand Prix (Open 2/3)               Xinsong Lin       29th
Stage 1 - Grand Prix (Masters 45+ 1/2/3/4)    Tim Guy           15th
Stage 2 - Circuit Race (Open 4/5)             Aj Iracheta       4th
...
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
5. Enter a race path when prompted (e.g. `2026/murrieta`).

## License

Apache 2.0 — see [LICENSE](LICENSE).
