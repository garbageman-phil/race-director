"""CLI entry point for race-director."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from race_director.config import load_config
from race_director.formatter import format_results
from race_director.scraper import scrape_race


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Scrape ontheday.net race results filtered by team name."
    )
    parser.add_argument(
        "--plain",
        action="store_true",
        default=False,
        help="Output results as a plain-text table instead of the default Markdown.",
    )
    parser.add_argument(
        "--race-path",
        metavar="PATH",
        default=None,
        help="Race path (e.g. 2026/murrieta). If omitted, you are prompted interactively.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        default=False,
        help="Suppress the configured team names banner (useful with --race-path).",
    )
    parser.add_argument(
        "--config",
        type=Path,
        default=None,
        metavar="FILE",
        help="Path to config.yaml (default: ./config.yaml in the current directory).",
    )
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = load_config(args.config)
    team_lower = config.team_names_lower()

    if not args.quiet:
        print("Configured team names:")
        for name in config.team_names:
            print(f"  - {name}")
        print()

    if args.race_path is not None:
        race_path = args.race_path.strip()
    else:
        race_path = input("Enter race path (e.g. 2026/murrieta): ").strip()

    if not race_path:
        print("Error: race path cannot be empty.", file=sys.stderr)
        raise SystemExit(1)

    print(f"\nFetching results from ontheday.net/{race_path}/ ...\n")

    try:
        outcome = scrape_race(race_path, team_lower)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if not outcome.finish and not outcome.primes and not outcome.mar:
        print("No results found for the configured team names.")
        raise SystemExit(0)

    print()
    print(format_results(outcome, markdown=not args.plain))


if __name__ == "__main__":
    main()
