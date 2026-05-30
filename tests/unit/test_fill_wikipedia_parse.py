"""T015: Unit tests for fill/channels/wikipedia.py — pure parsers only.

Real-call parts (search_and_fetch network) are gated behind LLMXIVE_REAL_TESTS.
"""

from __future__ import annotations

import os

import pytest

from llmxive.fill.channels.wikipedia import _parse_search, _parse_extract


# ---------------------------------------------------------------------------
# _parse_search — pure parser for action=query&list=search JSON
# ---------------------------------------------------------------------------

SEARCH_FIXTURE = {
    "query": {
        "search": [
            {"title": "Knot theory", "pageid": 17351},
            {"title": "Prime knot", "pageid": 23422},
            {"title": "Alternating knot", "pageid": 88771},
        ]
    }
}

SEARCH_FIXTURE_EMPTY = {
    "query": {
        "search": []
    }
}

SEARCH_FIXTURE_MISSING_KEY = {}


class TestParseSearch:
    def test_returns_titles(self):
        result = _parse_search(SEARCH_FIXTURE)
        assert result == ["Knot theory", "Prime knot", "Alternating knot"]

    def test_empty_results(self):
        assert _parse_search(SEARCH_FIXTURE_EMPTY) == []

    def test_missing_key(self):
        assert _parse_search(SEARCH_FIXTURE_MISSING_KEY) == []

    def test_preserves_order(self):
        fixture = {
            "query": {
                "search": [
                    {"title": "Z article"},
                    {"title": "A article"},
                ]
            }
        }
        assert _parse_search(fixture) == ["Z article", "A article"]

    def test_skips_missing_title(self):
        fixture = {
            "query": {
                "search": [
                    {"title": "Good article"},
                    {"pageid": 999},  # no title
                ]
            }
        }
        result = _parse_search(fixture)
        assert result == ["Good article"]


# ---------------------------------------------------------------------------
# _parse_extract — pure parser for action=query&prop=extracts JSON
# ---------------------------------------------------------------------------

EXTRACT_FIXTURE = {
    "query": {
        "pages": {
            "23422": {
                "pageid": 23422,
                "title": "Prime knot",
                "extract": (
                    "In knot theory, a prime knot is a knot that is, in a certain sense, "
                    "indecomposable. Knots are studied by crossing number. "
                    "At 13 crossings there are 9988 prime knots."
                ),
            }
        }
    }
}

EXTRACT_FIXTURE_MISSING = {
    "query": {
        "pages": {
            "-1": {
                "ns": 0,
                "title": "Missing article",
                "missing": "",
            }
        }
    }
}

EXTRACT_FIXTURE_EMPTY_EXTRACT = {
    "query": {
        "pages": {
            "100": {
                "pageid": 100,
                "title": "Some article",
                "extract": "",
            }
        }
    }
}


class TestParseExtract:
    def test_returns_title_and_text(self):
        result = _parse_extract(EXTRACT_FIXTURE)
        assert result is not None
        title, text = result
        assert title == "Prime knot"
        assert "9988" in text

    def test_missing_page_returns_none(self):
        assert _parse_extract(EXTRACT_FIXTURE_MISSING) is None

    def test_empty_extract_returns_none(self):
        assert _parse_extract(EXTRACT_FIXTURE_EMPTY_EXTRACT) is None

    def test_no_pages_key(self):
        assert _parse_extract({}) is None

    def test_multiple_pages_returns_first_valid(self):
        fixture = {
            "query": {
                "pages": {
                    "1": {
                        "pageid": 1,
                        "title": "Article One",
                        "extract": "Some text about article one.",
                    }
                }
            }
        }
        result = _parse_extract(fixture)
        assert result is not None
        title, text = result
        assert title == "Article One"
        assert "article one" in text


# ---------------------------------------------------------------------------
# Real-call: search_and_fetch (gated)
# ---------------------------------------------------------------------------

def _make_claim():
    from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
    return Claim(
        claim_id="c_test0001",
        kind=ClaimKind.NUMERIC,
        raw_text="There are 9988 prime knots at 13 crossings.",
        canonical="9988",
        context="prime knots at 13 crossings",
        artifact_path="test/artifact.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence={},
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
        source_hash=None,
    )


@pytest.mark.skipif(
    not os.environ.get("LLMXIVE_REAL_TESTS"),
    reason="LLMXIVE_REAL_TESTS not set",
)
def test_wikipedia_search_and_fetch_real():
    from llmxive.fill.channels.wikipedia import search_and_fetch
    from llmxive.fill.models import FetchedSource

    claim = _make_claim()
    results = search_and_fetch("prime knots crossing number", claim)
    assert isinstance(results, list)
    # With network, should return at least one result
    assert len(results) >= 1
    for src in results:
        assert isinstance(src, FetchedSource)
        assert src.channel == "wikipedia"
        assert src.text  # non-empty
        assert src.url.startswith("https://en.wikipedia.org/wiki/")
