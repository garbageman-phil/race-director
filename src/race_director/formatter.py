"""Format race results for terminal output."""

from __future__ import annotations

from tabulate import tabulate

from race_director.scraper import RaceResult

_HEADERS = ["Race Name", "Rider Name", "Rider Place"]


def _build_rows(results: list[RaceResult]) -> list[list[str]]:
    return [
        [
            f"{r.stage_name} ({r.category_name})" if r.stage_name else r.category_name,
            r.rider_name,
            r.place,
        ]
        for r in results
    ]


def format_results(results: list[RaceResult], *, markdown: bool = True) -> str:
    """Return a formatted string of race results.

    Args:
        results: Filtered list of race results to display.
        markdown: When True, output GitHub-Flavored Markdown table with heading.
    """
    rows = _build_rows(results)
    count = len(results)

    if markdown:
        table = tabulate(rows, headers=_HEADERS, tablefmt="github")
        return f"## Race Results\n\n{table}\n\n**{count} result(s) found.**"

    table = tabulate(rows, headers=_HEADERS, tablefmt="simple")
    return f"{table}\n\n{count} result(s) found."
