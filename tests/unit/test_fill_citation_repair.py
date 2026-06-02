"""T011 — unit tests for fill/citation_repair.py::repair_citation (pure)."""

from __future__ import annotations

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

    def test_inserted_citation_keeps_separator_before_next_word(self):
        # Lost-separator regression: when the value is followed by a word, the
        # inserted "(...)" must not abut it ("...A002863)prime"); a single space
        # must separate the citation from the following word.
        import re

        text = "There are 9988 prime knots at 13 crossings."
        result = repair_citation(text, claim=_claim(), provenance=_prov())
        assert not re.search(r"A002863\)[A-Za-z0-9]", result), result
        assert "prime knots" in result  # the following word survives intact

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


# ---------------------------------------------------------------------------
# Regression: a small numeric value ("2") must not match inside a larger
# number ("2026") and must be scoped to the claim's own sentence.
# ---------------------------------------------------------------------------


class TestRepairCitationNumericBoundaryScoping:
    def _bridge_claim(self) -> Claim:
        raw = "The trefoil is a 2-bridge knot in standard knot tables"
        return Claim(
            claim_id="c_bridge",
            kind=ClaimKind.NUMERIC,
            raw_text=raw,
            canonical=raw,
            context="knot theory bridge number",
            artifact_path="spec.md",
            source_type="external",
            status=ClaimStatus.NOT_ENOUGH_INFO,
            resolved_value="2",
            evidence=None,
            resolver=None,
            attempts=0,
            updated_at="2026-01-01T00:00:00Z",
        )

    def _bridge_prov(self) -> FillProvenance:
        return FillProvenance(
            value="2",
            source_id="2-bridge_knot",
            url="https://en.wikipedia.org/wiki/2-bridge_knot",
            quote="2-bridge knot",
            channel="wikipedia",
            conflicts=[],
        )

    def test_does_not_split_date_in_frontmatter(self):
        """The exact production corruption: value '2' must not land inside '2026'."""
        text = (
            "**Created**: 2026-05-29\n\n"
            "The trefoil is a 2-bridge knot in standard knot tables.\n"
        )
        result = repair_citation(
            text, claim=self._bridge_claim(), provenance=self._bridge_prov()
        )
        # The date token must remain intact — never split by an inserted citation.
        assert "2026-05-29" in result, f"date was split: {result!r}"
        assert "2 (Wikipedia" not in result.split("\n")[0], (
            f"citation injected into the date line: {result!r}"
        )
        # If a citation was inserted at all, it must be on the bridge-number line.
        if "Wikipedia" in result:
            bridge_line = next(
                ln for ln in result.splitlines() if "2-bridge knot" in ln
            )
            assert "Wikipedia" in bridge_line, (
                f"citation not adjacent to the bridge sentence: {result!r}"
            )

    def test_unrelated_standalone_two_not_cited(self):
        """A standalone '2' far from the claim's sentence must not be cited."""
        text = (
            "The study uses at least 2 regression model types.\n\n"
            "Knot theory has a long history.\n"
        )
        result = repair_citation(
            text, claim=self._bridge_claim(), provenance=self._bridge_prov()
        )
        # The bridge sentence/anchor is absent, so no citation may be inserted.
        assert result == text, (
            f"citation wrongly injected near unrelated '2': {result!r}"
        )

    def test_multi_digit_standalone_value_still_repaired(self):
        """Regression guard: standalone multi-digit values still get cited."""
        text = "There are 9988 prime knots at 13 crossings."
        result = repair_citation(text, claim=_claim(), provenance=_prov())
        assert "A002863" in result and "oeis.org" in result
        assert "9988" in result
