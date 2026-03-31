"""Scrape ontheday.net race results and filter by team name."""

from __future__ import annotations

import re
from dataclasses import dataclass
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup, Tag

BASE_URL = "https://www.ontheday.net"
_TIMEOUT = 30


@dataclass
class RaceResult:
    stage_name: str
    category_name: str
    rider_name: str
    place: str  # ordinal like "1st" or "DNP"


def _get(url: str) -> BeautifulSoup:
    resp = requests.get(url, timeout=_TIMEOUT)
    resp.raise_for_status()
    return BeautifulSoup(resp.text, "lxml")


def _ordinal(n: int) -> str:
    if 11 <= (n % 100) <= 13:
        return f"{n}th"
    suffix = {1: "st", 2: "nd", 3: "rd"}.get(n % 10, "th")
    return f"{n}{suffix}"


def _extract_stage_name(link_text: str) -> str:
    """Turn 'Mar 28 – Stage 1 - Grand Prix' into 'Stage 1 - Grand Prix'."""
    match = re.search(r"(Stage\s+\d+\s*[-–]\s*.+)", link_text)
    if match:
        return match.group(1).replace("–", "-").strip()
    return link_text.strip()


def _title_case_name(first: str, last: str) -> str:
    return f"{first.strip()} {last.strip()}".title()


def discover_stages(race_path: str) -> list[tuple[str, str]]:
    """Return (stage_display_name, stage_url) pairs for a race event."""
    url = f"{BASE_URL}/{race_path.strip('/')}/"
    soup = _get(url)

    stages: list[tuple[str, str]] = []
    seen_urls: set[str] = set()

    for a_tag in soup.select("a[href]"):
        href = a_tag["href"]
        if isinstance(href, list):
            href = href[0]
        if "@" not in href or "/results" in href:
            continue
        full_url = urljoin(url, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)
        stage_name = _extract_stage_name(a_tag.get_text(" ", strip=True))
        stages.append((stage_name, full_url))

    return stages


def _discover_results_urls(stage_url: str) -> list[str]:
    """Find all full-results page URLs from a stage page."""
    soup = _get(stage_url)

    urls: list[str] = []
    seen: set[str] = set()

    for a_tag in soup.select("a[href]"):
        href = a_tag["href"]
        if isinstance(href, list):
            href = href[0]
        text = a_tag.get_text(" ", strip=True).replace("\xa0", " ").lower()
        if "full results" not in text:
            continue
        base_href = href.split("#")[0]
        full_url = urljoin(stage_url, base_href)
        if full_url not in seen:
            seen.add(full_url)
            urls.append(full_url)

    return urls


def _is_results_table(table: Tag) -> bool:
    """Heuristic: a results table has a 'Place' column header."""
    first_th = table.find("th")
    if first_th:
        return first_th.get_text(strip=True).lower() == "place"
    return False


def _find_category_for_table(table: Tag) -> str | None:
    """Walk backwards from a table to find its category heading.

    Returns the most specific heading (h4 beats h3).  Skips headings
    that indicate non-results sections (primes, classification, finish order).
    """
    skip_patterns = re.compile(
        r"(prime|classification|finish order|omnium|compiled|stage results)",
        re.IGNORECASE,
    )

    for sibling in table.previous_elements:
        if not isinstance(sibling, Tag):
            continue
        if sibling.name in ("h4", "h3"):
            heading_text = sibling.get_text(" ", strip=True)
            if skip_patterns.search(heading_text):
                return None
            heading_text = re.sub(r"^Results:\s*", "", heading_text).strip()
            return heading_text
    return None


def _parse_results_page(
    results_url: str,
    stage_name: str,
    team_names_lower: set[str],
) -> list[RaceResult]:
    """Parse a full-results page and return matching team results."""
    soup = _get(results_url)
    matches: list[RaceResult] = []

    for table in soup.find_all("table"):
        if not _is_results_table(table):
            continue

        category = _find_category_for_table(table)
        if category is None:
            continue

        headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
        try:
            place_idx = headers.index("place")
            first_idx = headers.index("first")
            last_idx = headers.index("last")
        except ValueError:
            continue

        team_idx: int | None = None
        for candidate in ("team", "team name"):
            if candidate in headers:
                team_idx = headers.index(candidate)
                break

        if team_idx is None:
            continue

        for row in table.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) <= max(place_idx, first_idx, last_idx, team_idx):
                continue

            team_text = cells[team_idx].get_text(" ", strip=True)
            if team_text.lower() not in team_names_lower:
                continue

            place_text = cells[place_idx].get_text(strip=True)
            first_name = cells[first_idx].get_text(strip=True)
            last_name = cells[last_idx].get_text(strip=True)

            if not first_name or not last_name:
                continue

            if place_text.isdigit():
                place_display = _ordinal(int(place_text))
            else:
                place_display = place_text.upper()

            matches.append(
                RaceResult(
                    stage_name=stage_name,
                    category_name=category,
                    rider_name=_title_case_name(first_name, last_name),
                    place=place_display,
                )
            )

    return matches


def scrape_race(race_path: str, team_names_lower: set[str]) -> list[RaceResult]:
    """Scrape all results for a race event and return team-filtered results."""
    stages = discover_stages(race_path)
    if not stages:
        raise RuntimeError(
            f"No stages found at {BASE_URL}/{race_path.strip('/')}/ — "
            "check that the race path is correct (e.g. '2026/murrieta')."
        )

    all_results: list[RaceResult] = []

    for stage_name, stage_url in stages:
        print(f"  Scanning {stage_name}...")
        results_urls = _discover_results_urls(stage_url)

        for results_url in results_urls:
            page_results = _parse_results_page(
                results_url, stage_name, team_names_lower
            )
            all_results.extend(page_results)

    return all_results
