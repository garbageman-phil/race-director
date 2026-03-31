"""CLI entry point for race-director."""

from __future__ import annotations

import sys

from tabulate import tabulate

from race_director.config import load_config
from race_director.scraper import scrape_race


def main() -> None:
    config = load_config()
    team_lower = config.team_names_lower()

    print("Configured team names:")
    for name in config.team_names:
        print(f"  - {name}")
    print()

    race_path = input("Enter race path (e.g. 2026/murrieta): ").strip()
    if not race_path:
        print("Error: race path cannot be empty.", file=sys.stderr)
        raise SystemExit(1)

    print(f"\nFetching results from ontheday.net/{race_path}/ ...\n")

    try:
        results = scrape_race(race_path, team_lower)
    except RuntimeError as exc:
        print(f"Error: {exc}", file=sys.stderr)
        raise SystemExit(1)

    if not results:
        print("No results found for the configured team names.")
        raise SystemExit(0)

    rows = [
        [
            f"{r.stage_name} ({r.category_name})",
            r.rider_name,
            r.place,
        ]
        for r in results
    ]

    print()
    print(
        tabulate(
            rows,
            headers=["Race Name", "Rider Name", "Rider Place"],
            tablefmt="simple",
        )
    )
    print(f"\n{len(results)} result(s) found.")


if __name__ == "__main__":
    main()
