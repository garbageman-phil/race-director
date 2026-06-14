"""Season summary models and aggregation helpers."""

from __future__ import annotations

from dataclasses import dataclass, field


@dataclass(frozen=True)
class RiderRaceCount:
    rider_name: str
    teams: tuple[str, ...]
    total_races: int


@dataclass(frozen=True)
class SeasonSummary:
    source: str
    year: int
    riders: list[RiderRaceCount] = field(default_factory=list)


@dataclass(frozen=True)
class SeasonRow:
    rider_name: str
    team_name: str
    races_entered: int


def normalize_name(name: str) -> str:
    return " ".join(name.strip().split()).title()


def summarize_rows(rows: list[SeasonRow], *, source: str, year: int) -> SeasonSummary:
    totals: dict[str, int] = {}
    teams_by_rider: dict[str, set[str]] = {}

    for row in rows:
        rider_key = normalize_name(row.rider_name)
        if not rider_key:
            continue

        totals[rider_key] = totals.get(rider_key, 0) + row.races_entered
        if rider_key not in teams_by_rider:
            teams_by_rider[rider_key] = set()
        if row.team_name.strip():
            teams_by_rider[rider_key].add(row.team_name.strip())

    riders = [
        RiderRaceCount(
            rider_name=rider_name,
            teams=tuple(sorted(teams_by_rider.get(rider_name, set()))),
            total_races=total_races,
        )
        for rider_name, total_races in totals.items()
    ]
    riders.sort(key=lambda r: (-r.total_races, r.rider_name))
    return SeasonSummary(source=source, year=year, riders=riders)
