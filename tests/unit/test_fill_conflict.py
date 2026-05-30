"""T009 — unit tests for fill/conflict.py::choose and channels_for routing."""

from __future__ import annotations

import pytest

from llmxive.claims.models import ClaimKind
from llmxive.fill.channels import AUTHORITY, channels_for
from llmxive.fill.conflict import choose
from llmxive.fill.models import FetchedSource


def _src(channel: str, source_id: str = "id1", value_text: str = "x") -> FetchedSource:
    return FetchedSource(
        channel=channel,
        source_id=source_id,
        url=f"https://example.com/{source_id}",
        title=None,
        text=value_text or "placeholder",
        authority=AUTHORITY[channel],
    )


# ---------------------------------------------------------------------------
# choose() — conflict resolution
# ---------------------------------------------------------------------------


class TestChoose:
    def test_single_candidate_no_conflicts(self):
        src = _src("oeis", "A002863", "9988")
        winner_src, winner_val, conflicts = choose([(src, "9988")])
        assert winner_src is src
        assert winner_val == "9988"
        assert conflicts == []

    def test_highest_authority_wins(self):
        """OEIS (authority=0) beats Wikipedia (authority=2) even if listed second."""
        oeis = _src("oeis", "A002863", "9988")
        wiki = _src("wikipedia", "Prime_knot", "9988")
        winner_src, winner_val, conflicts = choose([(wiki, "9988"), (oeis, "9988")])
        assert winner_src is oeis
        assert winner_val == "9988"

    def test_conflict_recorded_when_values_differ(self):
        """Lower-authority source with DIFFERENT value → recorded in conflicts."""
        oeis = _src("oeis", "A002863", "9988")
        wiki = _src("wikipedia", "Prime_knot", "27635")
        winner_src, winner_val, conflicts = choose([(oeis, "9988"), (wiki, "27635")])
        assert winner_val == "9988"
        assert len(conflicts) == 1
        c = conflicts[0]
        assert c["value"] == "27635"
        assert c["source_id"] == "Prime_knot"
        assert c["channel"] == "wikipedia"
        assert "url" in c

    def test_agreeing_lower_authority_not_in_conflicts(self):
        """Lower-authority source with SAME value is NOT a conflict."""
        oeis = _src("oeis", "A002863", "9988")
        wiki = _src("wikipedia", "Prime_knot", "9988")
        _, _, conflicts = choose([(oeis, "9988"), (wiki, "9988")])
        assert conflicts == []

    def test_multiple_conflicts_all_recorded(self):
        """Never drop a conflict — all lower-authority disagreements must appear."""
        oeis = _src("oeis", "A002863", "9988")
        wiki = _src("wikipedia", "Prime_knot", "27635")
        paper = _src("paper", "arxiv123", "10000")
        _, winner_val, conflicts = choose([(oeis, "9988"), (wiki, "27635"), (paper, "10000")])
        assert winner_val == "9988"
        assert len(conflicts) == 2
        conflict_vals = {c["value"] for c in conflicts}
        assert "27635" in conflict_vals
        assert "10000" in conflict_vals

    def test_wikidata_beats_wikipedia_beats_paper(self):
        wikidata = _src("wikidata", "Q142", "Paris")
        wikipedia = _src("wikipedia", "France", "Lyon")
        paper = _src("paper", "doi123", "Bordeaux")
        winner_src, winner_val, conflicts = choose([
            (paper, "Bordeaux"), (wikipedia, "Lyon"), (wikidata, "Paris")
        ])
        assert winner_src is wikidata
        assert winner_val == "Paris"
        assert len(conflicts) == 2

    def test_empty_candidates_raises(self):
        with pytest.raises((ValueError, IndexError)):
            choose([])

    def test_deterministic_ordering(self):
        """Same input → same output regardless of list order."""
        oeis = _src("oeis", "A002863", "9988")
        wiki = _src("wikipedia", "Prime_knot", "27635")
        r1 = choose([(oeis, "9988"), (wiki, "27635")])
        r2 = choose([(wiki, "27635"), (oeis, "9988")])
        assert r1[1] == r2[1] == "9988"


# ---------------------------------------------------------------------------
# AUTHORITY map
# ---------------------------------------------------------------------------


class TestAuthorityMap:
    def test_oeis_highest(self):
        assert AUTHORITY["oeis"] < AUTHORITY["wikidata"]
        assert AUTHORITY["oeis"] < AUTHORITY["wikipedia"]
        assert AUTHORITY["oeis"] < AUTHORITY["theorem"]
        assert AUTHORITY["oeis"] < AUTHORITY["paper"]

    def test_wikidata_beats_wikipedia(self):
        assert AUTHORITY["wikidata"] < AUTHORITY["wikipedia"]

    def test_wikipedia_beats_theorem(self):
        assert AUTHORITY["wikipedia"] < AUTHORITY["theorem"]

    def test_theorem_beats_paper(self):
        assert AUTHORITY["theorem"] < AUTHORITY["paper"]


# ---------------------------------------------------------------------------
# channels_for() routing
# ---------------------------------------------------------------------------


class TestChannelsFor:
    def test_numeric_non_math(self):
        ch = channels_for(ClaimKind.NUMERIC, math=False)
        assert "oeis" in ch
        assert "wikipedia" in ch
        assert "paper" in ch
        assert "theorem" not in ch

    def test_numeric_math_includes_theorem(self):
        ch = channels_for(ClaimKind.NUMERIC, math=True)
        assert "theorem" in ch

    def test_entity_fact(self):
        ch = channels_for(ClaimKind.ENTITY_FACT, math=False)
        assert "wikidata" in ch
        assert "wikipedia" in ch
        assert "paper" in ch
        assert "oeis" not in ch

    def test_magnitude_returns_wikidata_wikipedia_paper(self):
        # spec 018 T020: MAGNITUDE is now fillable via wikidata/wikipedia/paper
        ch = channels_for(ClaimKind.MAGNITUDE, math=False)
        assert "wikidata" in ch
        assert "wikipedia" in ch
        assert "paper" in ch

    def test_relational_returns_wikidata_wikipedia_paper(self):
        # spec 018 T023: RELATIONAL is now fillable via wikidata/wikipedia/paper
        ch = channels_for(ClaimKind.RELATIONAL, math=False)
        assert "wikidata" in ch
        assert "wikipedia" in ch
        assert "paper" in ch

    def test_causal_returns_empty(self):
        assert channels_for(ClaimKind.CAUSAL, math=False) == []

    def test_citation_returns_empty(self):
        assert channels_for(ClaimKind.CITATION, math=False) == []

    def test_result_returns_empty(self):
        assert channels_for(ClaimKind.RESULT, math=False) == []
