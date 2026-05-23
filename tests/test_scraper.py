"""Unit tests for ontheday table parsing (no network)."""

from __future__ import annotations

import unittest
from pathlib import Path

from bs4 import BeautifulSoup

from race_director.scraper import (
    _parse_finish_table,
    _parse_mar_table,
    _parse_primes_table,
    _parse_results_page,
    _validate_race_page_url,
)


def _fixture(name: str) -> str:
    return (Path(__file__).parent / "fixtures" / name).read_text(encoding="utf-8")


class ValidateRacePageUrlTests(unittest.TestCase):
    def test_accepts_exact_match(self) -> None:
        _validate_race_page_url(
            "2026/eldo-1-8",
            "https://www.ontheday.net/2026/eldo-1-8/",
        )

    def test_accepts_subpath(self) -> None:
        _validate_race_page_url(
            "2026/gsrs",
            "https://www.ontheday.net/2026/gsrs/classification/",
        )

    def test_rejects_homepage_redirect(self) -> None:
        with self.assertRaises(RuntimeError) as ctx:
            _validate_race_page_url(
                "2026/eldo_1_8",
                "https://www.ontheday.net/",
            )
        self.assertIn("redirected away", str(ctx.exception))


class ParseFinishTableTests(unittest.TestCase):
    def test_skips_mar_section_heading(self) -> None:
        html = """
        <html><body>
        <h4>Most Assertive Rider (MAR) – Demo</h4>
        <table>
        <tr><th>Place</th><th>#</th><th>First</th><th>Last</th><th>Cat</th><th>Team</th></tr>
        <tr><td>1</td><td>1</td><td>Jane</td><td>Doe</td><td>3</td><td>Alpha Squad</td></tr>
        </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table")
        assert table is not None
        out = _parse_finish_table(table, "", {"alpha squad"})
        self.assertEqual(out, [])

    def test_parses_results_heading(self) -> None:
        html = """
        <html><body>
        <h3>Results: Open 4/5</h3>
        <table>
        <tr><th>Place</th><th>#</th><th>First</th><th>Last</th><th>Cat</th><th>Team</th></tr>
        <tr><td>3</td><td>9</td><td>Jane</td><td>Doe</td><td>4</td><td>Alpha Squad</td></tr>
        </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table")
        assert table is not None
        out = _parse_finish_table(table, "Stage 1", {"alpha squad"})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].category_name, "Open 4/5")
        self.assertEqual(out[0].rider_name, "Jane Doe")
        self.assertEqual(out[0].place, "3rd")


class ParsePrimesTableTests(unittest.TestCase):
    def test_prime_row(self) -> None:
        html = """
        <html><body>
        <h3>Results: Masters 50+ (Cat 1-4)</h3>
        <h4>Primes</h4>
        <table>
        <tr><th>Prime</th><th>#</th><th>First</th><th>Last</th><th>Cat</th><th>Team</th><th>License</th><th>Age</th><th>Points</th></tr>
        <tr><td>Men 50+ #1</td><td>1</td><td>Jane</td><td>Doe</td><td>2</td><td>Alpha Squad</td><td>1</td><td>50</td><td>10</td></tr>
        </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table")
        assert table is not None
        out = _parse_primes_table(table, "", {"alpha squad"})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].prime_label, "Men 50+ #1")
        self.assertEqual(out[0].rider_name, "Jane Doe")
        self.assertEqual(out[0].points, "10")
        self.assertEqual(out[0].category_name, "Masters 50+ (Cat 1-4)")


class ParseMarTableTests(unittest.TestCase):
    def test_skips_lap_continuation_row(self) -> None:
        html = """
        <html><body>
        <h4>Most Assertive Rider (MAR) – Masters 50+ 1/2/3/4</h4>
        <table>
        <tr><th>Place</th><th>#</th><th>First</th><th>Last</th><th>Cat</th><th>Team</th><th>License</th><th>Age</th><th>Points</th></tr>
        <tr><td>=&nbsp;2</td><td>1</td><td>Jane</td><td>Doe</td><td>3</td><td>Alpha Squad</td><td>1</td><td>50</td><td>3</td></tr>
        <tr><td><i>» Laps: 1, 2 &amp; 3</i></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td><td></td></tr>
        </table>
        </body></html>
        """
        soup = BeautifulSoup(html, "lxml")
        table = soup.find("table")
        assert table is not None
        out = _parse_mar_table(table, "", {"alpha squad"})
        self.assertEqual(len(out), 1)
        self.assertEqual(out[0].place, "= 2")
        self.assertEqual(out[0].rider_name, "Jane Doe")


class ParseResultsPageWireTests(unittest.TestCase):
    def test_fixture_page_splits_finish_prime_mar(self) -> None:
        import race_director.scraper as s

        def fake_get(url: str) -> BeautifulSoup:
            return BeautifulSoup(_fixture("sample_results_page.html"), "lxml")

        orig = s._get
        s._get = fake_get
        try:
            outcome = _parse_results_page("http://example.test/x", "", {"alpha squad"})
        finally:
            s._get = orig

        self.assertEqual(len(outcome.finish), 1)
        self.assertEqual(len(outcome.primes), 1)
        self.assertEqual(len(outcome.mar), 1)
        self.assertEqual(outcome.finish[0].rider_name, "Jane Doe")
        self.assertEqual(outcome.primes[0].prime_label, "Prime A")
        self.assertEqual(outcome.mar[0].place, "= 2")


if __name__ == "__main__":
    unittest.main()
