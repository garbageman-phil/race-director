"""Tests for season-summary aggregation and road-results provider parsing."""

from __future__ import annotations

from race_director.formatter import format_season_summary
from race_director.providers.road_results import fetch_road_results_rows
from race_director.season_summary import SeasonRow, summarize_rows


def test_summarize_rows_groups_and_sorts() -> None:
    rows = [
        SeasonRow(rider_name="jane doe", team_name="Alpha Team", races_entered=3),
        SeasonRow(rider_name="Jane   Doe", team_name="Alpha Team", races_entered=2),
        SeasonRow(rider_name="Bob Smith", team_name="Beta Team", races_entered=4),
    ]

    summary = summarize_rows(rows, source="road-results", year=2026)

    assert [r.rider_name for r in summary.riders] == ["Jane Doe", "Bob Smith"]
    assert [r.total_races for r in summary.riders] == [5, 4]
    assert summary.riders[0].teams == ("Alpha Team",)


def test_format_season_summary_markdown() -> None:
    summary = summarize_rows(
        [SeasonRow(rider_name="Jane Doe", team_name="Alpha Team", races_entered=3)],
        source="road-results",
        year=2026,
    )
    out = format_season_summary(summary, markdown=True)
    assert "## Season Summary (road-results, 2026)" in out
    assert "| Rider Name" in out
    assert "Jane Doe" in out
    assert "**1 rider(s).**" in out


def test_fetch_road_results_rows_uses_team_pages_and_racer_pages(monkeypatch) -> None:
    team_html = """
    <html><body>
      <h1>San Diego Bicycle Club powered by Bonnici Law Group</h1>
      <a href="/racer/226164">Doug Small</a>
      <a href="/racer/999999">Other Racer</a>
    </body></html>
    """
    doug_html = """
    <html><body>
      <h1>Doug Small</h1>
      <table>
        <tr><td>2026-01-01</td><td>Race A</td></tr>
        <tr><td>2026-02-01</td><td>Race B</td></tr>
        <tr><td>2025-05-01</td><td>Race C</td></tr>
      </table>
    </body></html>
    """
    other_html = """
    <html><body>
      <h1>Other Racer</h1>
      <table>
        <tr><td>2026-03-01</td><td>Race D</td></tr>
      </table>
    </body></html>
    """

    class _Resp:
        def __init__(self, text: str) -> None:
            self.text = text

        def raise_for_status(self) -> None:
            return None

    def fake_get(self: object, url: str, timeout: int) -> _Resp:
        assert timeout > 0
        if "team/73621" in url:
            return _Resp(team_html)
        if "racer/226164" in url:
            return _Resp(doug_html)
        if "racer/999999" in url:
            return _Resp(other_html)
        raise AssertionError(f"unexpected url: {url}")

    monkeypatch.setattr(
        "race_director.providers.road_results.requests.Session.get",
        fake_get,
    )
    rows = fetch_road_results_rows(
        year=2026,
        team_names_lower={"sdbc"},
        configured_team_links=["https://www.road-results.com/team/73621"],
    )
    assert len(rows) == 2
    by_name = {row.rider_name: row.races_entered for row in rows}
    assert by_name["Doug Small"] == 2
    assert by_name["Other Racer"] == 1
