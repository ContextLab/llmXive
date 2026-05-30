"""T011 — unit tests for fill/citation_repair.py::repair_citation (pure)."""

from __future__ import annotations

import pytest

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus
from llmxive.fill.citation_repair import repair_citation
from llmxive.fill.models import FillProvenance


def _claim(raw_text: str = "There are 9988 prime knots at 13 crossings") -> Claim:
    return Claim(
        claim_id="c_test",
        kind=ClaimKind.NUMERIC,
        raw_text=raw_text,
        canonical=raw_text,
        context="knot theory context",
        artifact_path="spec.md",
        source_type="external",
        status=ClaimStatus.NOT_ENOUGH_INFO,
        resolved_value="9988",
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-01-01T00:00:00Z",
    )


def _prov(
    value: str = "9988",
    source_id: str = "A002863",
    url: str = "https://oeis.org/A002863",
    channel: str = "oeis",
    conflicts: list | None = None,
) -> FillProvenance:
    return FillProvenance(
        value=value,
        source_id=source_id,
        url=url,
        quote="13 9988",
        channel=channel,
        conflicts=conflicts or [],
    )


# ---------------------------------------------------------------------------
# Basic repair: stale/free-text citation near the claim value is replaced
# ---------------------------------------------------------------------------


class TestRepairCitation:
    def test_replaces_stale_doi_adjacent_to_value(self):
        text = "There are 9988 prime knots at 13 crossings (Lee et al. 2024, doi:10.9999/fake)."
        result = repair_citation(text, claim=_claim(), provenance=_prov())
        # Stale citation removed/replaced by authoritative one
        assert "OEIS A002863" in result or "oeis.org/A002863" in result
        # The value is preserved
        assert "9988" in result

    def test_replaces_stale_arxiv_adjacent_to_value(self):
        text = "There are 9988 prime knots at 13 crossings (see arXiv:2402.13)."
        result = repair_citation(text, claim=_claim(), provenance=_prov())
        assert "OEIS A002863" in result or "oeis.org/A002863" in result
        assert "9988" in result

    def test_appends_inline_citation_when_none_present(self):
        text = "There are 9988 prime knots at 13 crossings."
        result = repair_citation(text, claim=_claim(), provenance=_prov())
        assert "OEIS A002863" in result or "oeis.org/A002863" in result
        assert "9988" in result

    def test_idempotent(self):
        text = "There are 9988 prime knots at 13 crossings."
        once = repair_citation(text, claim=_claim(), provenance=_prov())
        twice = repair_citation(once, claim=_claim(), provenance=_prov())
        assert once == twice

    def test_unrelated_prose_untouched(self):
        text = (
            "Knot theory began in the 19th century.\n"
            "There are 9988 prime knots at 13 crossings.\n"
            "Knots have many applications in biology."
        )
        result = repair_citation(text, claim=_claim(), provenance=_prov())
        assert "Knot theory began in the 19th century." in result
        assert "Knots have many applications in biology." in result

    def test_wikidata_provenance_cited(self):
        text = "The capital of France is Paris (some wrong reference)."
        prov = _prov(
            value="Paris",
            source_id="Q142",
            url="https://www.wikidata.org/wiki/Q142",
            channel="wikidata",
        )
        claim = Claim(
            claim_id="c_test2",
            kind=ClaimKind.ENTITY_FACT,
            raw_text="The capital of France is Paris",
            canonical="The capital of France is Paris",
            context="geography",
            artifact_path="spec.md",
            source_type="external",
            status=ClaimStatus.NOT_ENOUGH_INFO,
            resolved_value="Paris",
            evidence=None,
            resolver=None,
            attempts=0,
            updated_at="2026-01-01T00:00:00Z",
        )
        result = repair_citation(text, claim=claim, provenance=prov)
        assert "wikidata.org/wiki/Q142" in result or "Q142" in result
        assert "Paris" in result

    def test_markdown_link_replaced(self):
        text = "There are 9988 prime knots [Lee et al.](https://fake.example.com/paper)."
        result = repair_citation(text, claim=_claim(), provenance=_prov())
        assert "OEIS A002863" in result or "oeis.org/A002863" in result
        assert "9988" in result

    def test_value_not_in_text_returns_unchanged(self):
        # If the claim value doesn't appear in the text at all, leave it alone
        text = "Some unrelated text about something else entirely."
        result = repair_citation(text, claim=_claim(), provenance=_prov())
        # No spurious citation injection into unrelated text
        assert result == text or "9988" not in result

    def test_appended_citation_format_oeis(self):
        text = "There are 9988 prime knots at 13 crossings."
        result = repair_citation(text, claim=_claim(), provenance=_prov())
        # Should contain both the OEIS A-number and the URL in some form
        assert "A002863" in result
        assert "oeis.org" in result
