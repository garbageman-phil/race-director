"""Format race results for terminal output."""

from __future__ import annotations

from tabulate import tabulate

from race_director.scraper import MarResult, PrimeResult, RaceResult, ScrapeOutcome

_FINISH_HEADERS = ["Race Name", "Rider Name", "Rider Place"]
_PRIME_HEADERS = ["Race Name", "Rider Name", "Prime", "Points"]
_MAR_HEADERS = ["Race Name", "Rider Name", "Place", "Points"]


def _finish_rows(results: list[RaceResult]) -> list[list[str]]:
    return [
        [
            f"{r.stage_name} ({r.category_name})" if r.stage_name else r.category_name,
            r.rider_name,
            r.place,
        ]
        for r in results
    ]


def _prime_rows(results: list[PrimeResult]) -> list[list[str]]:
    return [
        [
            f"{r.stage_name} ({r.category_name})" if r.stage_name else r.category_name,
            r.rider_name,
            r.prime_label,
            r.points,
        ]
        for r in results
    ]


def _mar_rows(results: list[MarResult]) -> list[list[str]]:
    return [
        [
            f"{r.stage_name} ({r.category_name})" if r.stage_name else r.category_name,
            r.rider_name,
            r.place,
            r.points,
        ]
        for r in results
    ]


def format_results(outcome: ScrapeOutcome, *, markdown: bool = True) -> str:
    """Return a formatted string of race results, primes, and MAR rows.

    Args:
        outcome: Scraped finish, primes, and MAR entries for the configured teams.
        markdown: When True, output GitHub-Flavored Markdown tables with headings.
    """
    parts: list[str] = []
    tablefmt = "github" if markdown else "simple"

    if outcome.finish:
        rows = _finish_rows(outcome.finish)
        table = tabulate(rows, headers=_FINISH_HEADERS, tablefmt=tablefmt)
        count = len(outcome.finish)
        if markdown:
            parts.append(f"## Race Results\n\n{table}\n\n**{count} finish result(s).**")
        else:
            parts.append(f"{table}\n\n{count} finish result(s).")

    if outcome.primes:
        rows = _prime_rows(outcome.primes)
        table = tabulate(rows, headers=_PRIME_HEADERS, tablefmt=tablefmt)
        count = len(outcome.primes)
        if markdown:
            parts.append(f"### Primes\n\n{table}\n\n**{count} prime result(s).**")
        else:
            parts.append(f"Primes\n\n{table}\n\n{count} prime result(s).")

    if outcome.mar:
        rows = _mar_rows(outcome.mar)
        table = tabulate(rows, headers=_MAR_HEADERS, tablefmt=tablefmt)
        count = len(outcome.mar)
        if markdown:
            parts.append(
                f"### Most Assertive Rider (MAR)\n\n{table}\n\n**{count} MAR result(s).**"
            )
        else:
            parts.append(
                f"Most Assertive Rider (MAR)\n\n{table}\n\n{count} MAR result(s)."
            )

    sep = "\n\n" if markdown else "\n\n"
    return sep.join(parts)
