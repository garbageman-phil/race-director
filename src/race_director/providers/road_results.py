"""Road-Results season summary provider via team and racer pages."""

from __future__ import annotations

import re
from urllib.parse import urljoin

import requests
from bs4 import BeautifulSoup

from race_director.season_summary import SeasonRow

_BASE_URL = "https://www.road-results.com"
_TIMEOUT = 30
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
    "Referer": _BASE_URL + "/",
}


def _normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text).strip()


def _to_int(text: str) -> int:
    digits = re.sub(r"[^\d]", "", text)
    if not digits:
        return 0
    return int(digits)


def _matches_team(team_text: str, team_names_lower: set[str]) -> bool:
    lowered = team_text.lower()
    simplified = re.sub(r"[^a-z0-9]+", "", lowered)
    for team_name in team_names_lower:
        team_simple = re.sub(r"[^a-z0-9]+", "", team_name.lower())
        if (
            lowered == team_name
            or team_name in lowered
            or lowered in team_name
            or (team_simple and team_simple in simplified)
        ):
            return True
    return False


def _fetch_html(session: requests.Session, url: str) -> str:
    resp = session.get(url, timeout=_TIMEOUT)
    resp.raise_for_status()
    return resp.text


def _extract_team_links(soup: BeautifulSoup) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not isinstance(href, str):
            continue
        if "/team/" not in href:
            continue
        full = urljoin(_BASE_URL + "/", href)
        if full in seen:
            continue
        seen.add(full)
        urls.append(full)
    return urls


def _discover_team_links(
    session: requests.Session,
    *,
    team_names_lower: set[str],
    debug: bool,
) -> list[str]:
    candidates = [f"{_BASE_URL}/", f"{_BASE_URL}/results", f"{_BASE_URL}/teams"]
    links: list[str] = []
    seen: set[str] = set()
    for url in candidates:
        try:
            html = _fetch_html(session, url)
        except requests.RequestException:
            continue
        soup = BeautifulSoup(html, "lxml")
        for a in soup.select("a[href]"):
            href = a.get("href")
            if not isinstance(href, str) or "/team/" not in href:
                continue
            label = _normalize(a.get_text(" ", strip=True))
            if label and not _matches_team(label, team_names_lower):
                continue
            full = urljoin(_BASE_URL + "/", href)
            if full in seen:
                continue
            seen.add(full)
            links.append(full)
    if debug:
        print(f"[season-debug] discovered team links: {len(links)}")
    return links


def _extract_racer_links(soup: BeautifulSoup) -> list[str]:
    urls: list[str] = []
    seen: set[str] = set()
    for a in soup.select("a[href]"):
        href = a.get("href")
        if not isinstance(href, str):
            continue
        if "/racer/" not in href:
            continue
        full = urljoin(_BASE_URL + "/", href)
        if full in seen:
            continue
        seen.add(full)
        urls.append(full)
    return urls


def _count_racer_year_rows(soup: BeautifulSoup, year: int) -> int:
    year_str = str(year)
    count = 0
    for row in soup.find_all("tr"):
        cells = row.find_all("td")
        if len(cells) < 2:
            continue
        row_text = _normalize(row.get_text(" ", strip=True))
        if year_str not in row_text:
            continue
        if "races entered" in row_text.lower():
            continue
        count += 1
    return count


def _team_name_from_page(soup: BeautifulSoup) -> str:
    h1 = soup.find("h1")
    if h1 is None:
        return ""
    return _normalize(h1.get_text(" ", strip=True))


def _rider_name_from_page(soup: BeautifulSoup, fallback_url: str) -> str:
    h1 = soup.find("h1")
    if h1 is not None:
        name = _normalize(h1.get_text(" ", strip=True))
        if name:
            return name
    return fallback_url.rsplit("/", 1)[-1]


def _make_session() -> requests.Session:
    session = requests.Session()
    session.headers.update(_HEADERS)
    return session


def fetch_road_results_rows(
    *,
    year: int,
    team_names_lower: set[str],
    configured_team_links: list[str] | None = None,
    debug: bool = False,
) -> list[SeasonRow]:
    """Fetch season rows by traversing team pages and each rider page."""
    session = _make_session()
    team_links = list(configured_team_links or [])
    if not team_links:
        team_links = _discover_team_links(
            session,
            team_names_lower=team_names_lower,
            debug=debug,
        )
    if debug:
        print(f"[season-debug] using team links: {len(team_links)}")
        for link in team_links:
            print(f"[season-debug]   {link}")

    rows: list[SeasonRow] = []
    seen_racers: set[str] = set()
    for team_link in team_links:
        team_html = _fetch_html(session, team_link)
        team_soup = BeautifulSoup(team_html, "lxml")
        team_name = _team_name_from_page(team_soup) or team_link

        racer_links = _extract_racer_links(team_soup)
        if debug:
            print(
                f"[season-debug] team '{team_name}' "
                f"racer links discovered: {len(racer_links)}"
            )

        for racer_link in racer_links:
            if racer_link in seen_racers:
                continue
            seen_racers.add(racer_link)

            racer_html = _fetch_html(session, racer_link)
            racer_soup = BeautifulSoup(racer_html, "lxml")
            rider_name = _rider_name_from_page(racer_soup, racer_link)
            races_entered = _count_racer_year_rows(racer_soup, year)
            if races_entered <= 0:
                continue

            rows.append(
                SeasonRow(
                    rider_name=rider_name,
                    team_name=team_name,
                    races_entered=races_entered,
                )
            )
            if debug:
                print(
                    f"[season-debug] rider '{rider_name}' -> {races_entered} race row(s) in {year}"
                )

    return rows
