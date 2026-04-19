"""Scrape ontheday.net race results and filter by team name."""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from urllib.parse import urljoin

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


@dataclass
class PrimeResult:
    stage_name: str
    category_name: str
    prime_label: str
    rider_name: str
    points: str


@dataclass
class MarResult:
    stage_name: str
    category_name: str
    place: str
    rider_name: str
    points: str


@dataclass
class ScrapeOutcome:
    finish: list[RaceResult] = field(default_factory=list)
    primes: list[PrimeResult] = field(default_factory=list)
    mar: list[MarResult] = field(default_factory=list)


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


def _normalize_whitespace(text: str) -> str:
    return re.sub(r"[\xa0\s]+", " ", text).strip()


def _discover_stages(
    soup: BeautifulSoup, base_url: str
) -> list[tuple[str, str]]:
    """Return (stage_display_name, stage_url) pairs from a race event page."""
    stages: list[tuple[str, str]] = []
    seen_urls: set[str] = set()

    for a_tag in soup.select("a[href]"):
        href = a_tag["href"]
        if isinstance(href, list):
            href = href[0]
        if "@" not in href or "/results" in href:
            continue
        full_url = urljoin(base_url, href)
        if full_url in seen_urls:
            continue
        seen_urls.add(full_url)
        stage_name = _extract_stage_name(a_tag.get_text(" ", strip=True))
        stages.append((stage_name, full_url))

    return stages


def _find_results_links(soup: BeautifulSoup, base_url: str) -> list[str]:
    """Extract deduplicated full-results page URLs from a parsed page."""
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
        full_url = urljoin(base_url, base_href)
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


def _is_primes_table(table: Tag) -> bool:
    first_th = table.find("th")
    if first_th:
        return first_th.get_text(strip=True).lower() == "prime"
    return False


def _nearest_section_heading(table: Tag) -> tuple[str, str] | None:
    """Return (tag_name, heading text) for nearest preceding h3 or h4."""
    for sibling in table.previous_elements:
        if not isinstance(sibling, Tag):
            continue
        if sibling.name in ("h3", "h4"):
            return sibling.name, sibling.get_text(" ", strip=True)
    return None


def _is_mar_table(table: Tag) -> bool:
    """MAR tables use Place columns but sit under a Most Assertive Rider heading."""
    if not _is_results_table(table):
        return False
    heading = _nearest_section_heading(table)
    if not heading:
        return False
    _, text = heading
    if re.match(r"Results:\s*", text, re.I):
        return False
    return bool(re.search(r"most assertive rider|\(mar\)", text, re.I))


def _find_category_for_finish_table(table: Tag) -> str | None:
    """Walk backwards from a table to find its category heading for finish results.

    Skips primes/classification sections and MAR / team standings headings.
    """
    skip_patterns = re.compile(
        r"(prime|classification|finish order|omnium|compiled|stage results)",
        re.IGNORECASE,
    )
    section_skip = re.compile(
        r"(most assertive rider|\(mar\)|^teams\b)",
        re.IGNORECASE,
    )

    for sibling in table.previous_elements:
        if not isinstance(sibling, Tag):
            continue
        if sibling.name in ("h4", "h3"):
            heading_text = sibling.get_text(" ", strip=True)
            if skip_patterns.search(heading_text):
                return None
            if section_skip.search(heading_text):
                return None
            heading_text = re.sub(r"^Results:\s*", "", heading_text).strip()
            return heading_text
    return None


def _find_results_h3_category(table: Tag) -> str | None:
    """Category label from the main 'Results: …' h3 above this section."""
    for sibling in table.previous_elements:
        if not isinstance(sibling, Tag):
            continue
        if sibling.name == "h3":
            heading_text = sibling.get_text(" ", strip=True)
            if re.match(r"Results:\s*", heading_text, re.I):
                return re.sub(r"^Results:\s*", "", heading_text).strip()
    return None


def _find_mar_category_label(table: Tag) -> str | None:
    """Heading text for a MAR table (h4 under the MAR section)."""
    for sibling in table.previous_elements:
        if not isinstance(sibling, Tag):
            continue
        if sibling.name in ("h4", "h3"):
            text = sibling.get_text(" ", strip=True)
            if re.search(r"most assertive rider|\(mar\)", text, re.I):
                return text.strip()
    return None


def _team_column_index(headers: list[str]) -> int | None:
    for candidate in ("team", "team name"):
        if candidate in headers:
            return headers.index(candidate)
    return None


def _parse_finish_table(
    table: Tag,
    stage_name: str,
    team_names_lower: set[str],
) -> list[RaceResult]:
    category = _find_category_for_finish_table(table)
    if category is None:
        return []

    headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
    try:
        place_idx = headers.index("place")
        first_idx = headers.index("first")
        last_idx = headers.index("last")
    except ValueError:
        return []

    team_idx = _team_column_index(headers)
    if team_idx is None:
        return []

    matches: list[RaceResult] = []
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


def _parse_primes_table(
    table: Tag,
    stage_name: str,
    team_names_lower: set[str],
) -> list[PrimeResult]:
    category = _find_results_h3_category(table) or ""
    headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
    try:
        prime_idx = headers.index("prime")
        first_idx = headers.index("first")
        last_idx = headers.index("last")
    except ValueError:
        return []

    team_idx = _team_column_index(headers)
    if team_idx is None:
        return []

    points_idx = headers.index("points") if "points" in headers else None

    matches: list[PrimeResult] = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if not cells:
            continue
        if len(cells) <= max(prime_idx, first_idx, last_idx, team_idx):
            continue

        prime_label = cells[prime_idx].get_text(" ", strip=True)
        if not prime_label or re.search(r"prime count", prime_label, re.I):
            continue
        if re.search(r"primes do not contribute", prime_label, re.I):
            continue

        team_text = cells[team_idx].get_text(" ", strip=True)
        if team_text.lower() not in team_names_lower:
            continue

        first_name = cells[first_idx].get_text(strip=True)
        last_name = cells[last_idx].get_text(strip=True)
        if not first_name or not last_name:
            continue

        points = ""
        if points_idx is not None and len(cells) > points_idx:
            points = cells[points_idx].get_text(strip=True)

        matches.append(
            PrimeResult(
                stage_name=stage_name,
                category_name=category,
                prime_label=prime_label,
                rider_name=_title_case_name(first_name, last_name),
                points=points,
            )
        )

    return matches


def _parse_mar_table(
    table: Tag,
    stage_name: str,
    team_names_lower: set[str],
) -> list[MarResult]:
    category = _find_mar_category_label(table) or ""
    headers = [th.get_text(strip=True).lower() for th in table.find_all("th")]
    try:
        place_idx = headers.index("place")
        first_idx = headers.index("first")
        last_idx = headers.index("last")
    except ValueError:
        return []

    team_idx = _team_column_index(headers)
    if team_idx is None:
        return []

    points_idx = headers.index("points") if "points" in headers else None

    matches: list[MarResult] = []
    for row in table.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) <= max(place_idx, first_idx, last_idx, team_idx):
            continue

        first_name = cells[first_idx].get_text(strip=True)
        last_name = cells[last_idx].get_text(strip=True)
        if not first_name or not last_name:
            continue

        team_text = cells[team_idx].get_text(" ", strip=True)
        if team_text.lower() not in team_names_lower:
            continue

        place_text = _normalize_whitespace(cells[place_idx].get_text(" ", strip=True))
        if not place_text or place_text.startswith("»") or "lap" in place_text.lower():
            continue

        points = ""
        if points_idx is not None and len(cells) > points_idx:
            points = _normalize_whitespace(cells[points_idx].get_text(strip=True))

        matches.append(
            MarResult(
                stage_name=stage_name,
                category_name=category,
                place=place_text,
                rider_name=_title_case_name(first_name, last_name),
                points=points,
            )
        )

    return matches


def _parse_results_page(
    results_url: str,
    stage_name: str,
    team_names_lower: set[str],
) -> ScrapeOutcome:
    """Parse a full-results page and return matching team results."""
    soup = _get(results_url)
    outcome = ScrapeOutcome()

    for table in soup.find_all("table"):
        if _is_primes_table(table):
            outcome.primes.extend(
                _parse_primes_table(table, stage_name, team_names_lower)
            )
        elif _is_mar_table(table):
            outcome.mar.extend(_parse_mar_table(table, stage_name, team_names_lower))
        elif _is_results_table(table):
            outcome.finish.extend(
                _parse_finish_table(table, stage_name, team_names_lower)
            )

    return outcome


def scrape_race(race_path: str, team_names_lower: set[str]) -> ScrapeOutcome:
    """Scrape all results for a race event and return team-filtered results.

    Handles both multi-stage events (e.g. Tour de Murrieta) and single-day
    races (e.g. CBR criteriums) where results links live on the main page.
    """
    race_url = f"{BASE_URL}/{race_path.strip('/')}/"
    race_soup = _get(race_url)

    stages = _discover_stages(race_soup, race_url)
    outcome = ScrapeOutcome()

    if stages:
        for stage_name, stage_url in stages:
            print(f"  Scanning {stage_name}...")
            stage_soup = _get(stage_url)
            results_urls = _find_results_links(stage_soup, stage_url)
            for results_url in results_urls:
                page = _parse_results_page(results_url, stage_name, team_names_lower)
                outcome.finish.extend(page.finish)
                outcome.primes.extend(page.primes)
                outcome.mar.extend(page.mar)
    else:
        results_urls = _find_results_links(race_soup, race_url)
        if not results_urls:
            raise RuntimeError(
                f"No stages or results found at {race_url} — "
                "check that the race path is correct (e.g. '2026/murrieta')."
            )
        print("  Single-day race — scanning results...")
        for results_url in results_urls:
            page = _parse_results_page(results_url, "", team_names_lower)
            outcome.finish.extend(page.finish)
            outcome.primes.extend(page.primes)
            outcome.mar.extend(page.mar)

    return outcome
