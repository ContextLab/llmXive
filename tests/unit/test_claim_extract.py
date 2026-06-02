"""T015 — Unit tests for claims/extract.py (T015).

Offline: exercises the REAL post-parse filter directly (no mock backend).
Real-LLM: gated behind LLMXIVE_REAL_TESTS.
"""

from __future__ import annotations

import os

import pytest

from llmxive.claims.extract import (
    _filter_check_worthy,
    _parse_extraction_reply,
    _tolerant_parse_claims,
    strip_nonclaim_sections,
)
from llmxive.claims.models import ClaimStatus


class TestFilterCheckWorthy:
    """Offline tests for the post-parse deterministic filter (no backend)."""

    def test_numeric_claim_kept(self):
        candidates = ["There are 9,988 prime knots at 10 crossings."]
        result = _filter_check_worthy(candidates)
        assert len(result) == 1
        assert result[0] == "There are 9,988 prime knots at 10 crossings."

    def test_design_choice_dropped(self):
        candidates = [
            "We use a threshold of p < 0.05.",
        ]
        result = _filter_check_worthy(candidates)
        assert len(result) == 0

    def test_parameter_setting_dropped(self):
        candidates = [
            "The learning rate is set to 0.001.",
        ]
        result = _filter_check_worthy(candidates)
        assert len(result) == 0

    def test_resolution_setting_dropped(self):
        candidates = ["Image resolution is 1200x900 pixels."]
        result = _filter_check_worthy(candidates)
        assert len(result) == 0

    def test_requirement_id_dropped(self):
        candidates = ["FR-001 requires the system to log all events."]
        result = _filter_check_worthy(candidates)
        assert len(result) == 0

    def test_subjective_statement_dropped(self):
        candidates = ["This approach is elegant and well-suited to the problem."]
        result = _filter_check_worthy(candidates)
        assert len(result) == 0

    def test_mixed_keeps_only_checkworthy(self):
        candidates = [
            "There are 9,988 prime knots at 10 crossings.",  # keep: numeric empirical
            "We use a threshold of p < 0.05.",               # drop: design choice
            "The approach is well-suited for the task.",     # drop: subjective
            "Knot theory was founded by Carl Friedrich Gauss.",  # keep: entity fact
        ]
        result = _filter_check_worthy(candidates)
        assert "There are 9,988 prime knots at 10 crossings." in result
        assert "Knot theory was founded by Carl Friedrich Gauss." in result
        for dropped in ["We use a threshold of p < 0.05.", "The approach is well-suited for the task."]:
            assert dropped not in result

    def test_empty_input(self):
        assert _filter_check_worthy([]) == []

    def test_empty_string_dropped(self):
        result = _filter_check_worthy([""])
        assert result == []

    def test_short_fragment_dropped(self):
        """Very short strings (< 10 chars) are not check-worthy claims."""
        result = _filter_check_worthy(["yes", "no"])
        assert result == []

    def test_promotional_standing_statement_dropped(self):
        """Fix D — a purely promotional 'standing' statement with no crisp
        checkable core is dropped (PROJ-552 root cause 5: it cannot be
        substantiated and would leave a residual [UNRESOLVED-CLAIM:] marker)."""
        candidates = [
            "The census is a well-established, peer-reviewed reference.",
            "This dataset is community-standard and widely used.",
            "Method X is the gold standard for this task.",
        ]
        assert _filter_check_worthy(candidates) == []

    def test_checkworthy_number_with_citation_survives_standing_language(self):
        """Fix D — the existing rule still holds: a statement with a salient
        NUMBER and an explicit citation passes even alongside standing language."""
        candidates = [
            "There are 9988 prime knots (OEIS A002863), a well-known catalog.",
        ]
        result = _filter_check_worthy(candidates)
        assert result == ["There are 9988 prime knots (OEIS A002863), a well-known catalog."]


class TestStripNonclaimSections:
    """Citation/survey sections (References, Related Work) are excluded from the
    text sent to the extractor — their citation years and titles must never become
    the document's own claims (the PROJ-552 garbage-fact root cause)."""

    _PROJ552 = (
        "# Feature Spec\n\n"
        "## User Scenarios\n\n"
        "The dataset covers 9,988 prime knots at crossing number 13.\n\n"
        "## Related Work\n\n"
        "- [Seifert circles ... and links (2022)](https://arxiv.org/abs/2212.14737)"
        " — Extends Ohyama's inequality.\n"
        "- [Minimal grid diagrams ... arc index 13 (2024)]"
        "(https://arxiv.org/abs/2402.02717) — Provides data on 9,988 prime knots.\n\n"
        "## Requirements\n\n"
        "- **FR-001**: System MUST download all knots with crossing number <= 13.\n\n"
        "## Assumptions\n\n"
        "The exact count is 9,988 prime knots, per OEIS A002863.\n\n"
        "## References\n\n"
        "1. Hoste, J. (1998). A Census of Knots. Exp. Math. 7(4), 281-299.\n"
    )

    def test_related_work_and_references_removed(self) -> None:
        out = strip_nonclaim_sections(self._PROJ552)
        # The citation years / referenced-paper metadata are gone.
        assert "Related Work" not in out
        assert "References" not in out
        assert "2022" not in out  # citation year never extractable
        assert "Hoste" not in out

    def test_body_sections_and_real_fact_preserved(self) -> None:
        out = strip_nonclaim_sections(self._PROJ552)
        # The body — and the REAL 9,988 claim with its OEIS citation — survive,
        # so masking Related Work never loses the verifiable fact.
        assert "FR-001" in out
        assert "OEIS A002863" in out
        assert "9,988 prime knots at crossing number 13" in out

    def test_identity_when_no_nonclaim_sections(self) -> None:
        doc = "## A\n\nThere are 5 things.\n\n## B\n\nAnd 7 others.\n"
        assert strip_nonclaim_sections(doc) == doc

    def test_heading_inside_code_fence_not_masked(self) -> None:
        doc = (
            "## Intro\n\n```python\n# References\nx = 13\n```\n\n"
            "## Body\n\nThere are 5 widgets.\n"
        )
        out = strip_nonclaim_sections(doc)
        assert "There are 5 widgets." in out  # Body not swallowed
        assert "x = 13" in out  # fenced code preserved

    def test_excluded_section_with_subsection_fully_removed(self) -> None:
        doc = (
            "## Body\n\nfoo 1.\n\n## Bibliography\n\n"
            "### Sub\n\nbar (1999).\n"
        )
        out = strip_nonclaim_sections(doc)
        assert "1999" not in out and "Sub" not in out
        assert "foo 1." in out

    def test_consecutive_excluded_sections_both_removed(self) -> None:
        doc = (
            "## Related Work\n\ncited (2020).\n\n"
            "## References\n\nWeeks (1998).\n\n"
            "## Requirements\n\nFR-002 here.\n"
        )
        out = strip_nonclaim_sections(doc)
        assert "2020" not in out and "Weeks" not in out
        assert "FR-002 here." in out


class TestParseExtractionReply:
    """Offline tests for the YAML reply parser + tolerant recovery (no backend).

    Regression: the extraction model routinely emits a verbatim ``claim_text``
    containing an embedded double-quoted paper title (e.g. ``"A Census of
    Knots."``). That breaks ``yaml.safe_load`` and previously dropped EVERY
    claim — a silent fabrication passthrough that let PROJ-552's wrong 27,635
    count survive un-flagged-and-un-filled.
    """

    def test_valid_yaml_fast_path(self):
        reply = (
            "claims:\n"
            '  - claim_text: "There are 9988 prime knots at 13 crossings."\n'
            '    canonical: "9988 prime knots at 13 crossings"\n'
            '    context: "Knot enumeration."\n'
            '    number: "9988"\n'
            '    source: "https://oeis.org/A002863"\n'
        )
        claims = _parse_extraction_reply(reply, "doc.md")
        assert len(claims) == 1
        assert "9988 prime knots" in claims[0].raw_text
        assert claims[0].status == ClaimStatus.PENDING

    def test_embedded_double_quotes_recovered(self):
        """The exact PROJ-552 failure mode: an embedded `"A Census of Knots."`
        title breaks strict YAML, but the tolerant parser recovers the claim."""
        reply = (
            "claims:\n"
            '  - claim_text: "For crossing number 13, the exact count is 27,635 '
            'prime knots as established in Hoste, J., Thistlethwaite, M. B., & '
            'Weeks, J. (1998). "A Census of Knots." Experimental Mathematics, '
            '7(4), 281-299."\n'
            '    canonical: "27635 prime knots at 13 crossings"\n'
            '    context: "Prime knot enumeration reference."\n'
            '    number: "27635"\n'
            '    source: "Hoste, Thistlethwaite & Weeks (1998)"\n'
        )
        # Strict YAML must fail on this input (proves the regression precondition)…
        import yaml
        with pytest.raises(yaml.YAMLError):
            yaml.safe_load(reply.strip())
        # …but the parser recovers exactly one claim with the wrong number intact
        # so the downstream resolver/fill can flag + correct it.
        claims = _parse_extraction_reply(reply, "doc.md")
        assert len(claims) == 1
        assert "27,635" in claims[0].raw_text
        assert "A Census of Knots." in claims[0].raw_text  # inner quote preserved
        assert claims[0].canonical == "27635 prime knots at 13 crossings"

    def test_code_fenced_embedded_quotes_recovered(self):
        reply = (
            "```yaml\n"
            "claims:\n"
            '  - claim_text: "The paper "Knots and Links" reports 12,965 entries."\n'
            '    canonical: "12965 entries"\n'
            "```\n"
        )
        claims = _parse_extraction_reply(reply, "doc.md")
        assert len(claims) == 1
        assert "12,965" in claims[0].raw_text

    def test_multiple_claims_recovered(self):
        reply = (
            "claims:\n"
            '  - claim_text: "Result one cites "Foo et al." with 100 cases."\n'
            '    canonical: "100 cases"\n'
            '  - claim_text: "Result two cites "Bar 2020." with 250 cases."\n'
            '    canonical: "250 cases"\n'
        )
        claims = _parse_extraction_reply(reply, "doc.md")
        assert len(claims) == 2
        assert "100 cases" in claims[0].canonical
        assert "250 cases" in claims[1].canonical

    def test_tolerant_parser_strips_number_inline_comment(self):
        raw = (
            "claims:\n"
            '  - claim_text: "Some claim with 42 items."\n'
            '    number: "42"  # the salient numeric value\n'
        )
        claims = _tolerant_parse_claims(raw, "doc.md")
        assert len(claims) == 1
        assert "42 items" in claims[0].raw_text

    def test_no_claims_returns_empty(self):
        assert _parse_extraction_reply("claims: []", "doc.md") == []
        assert _parse_extraction_reply("not yaml at all : : :", "doc.md") == []


@pytest.mark.skipif(
    not os.environ.get("LLMXIVE_REAL_TESTS"),
    reason="Real LLM call — set LLMXIVE_REAL_TESTS=1 to run",
)
class TestExtractClaimsRealLLM:
    """Real-LLM extraction (requires LLMXIVE_REAL_TESTS=1 and Dartmouth key)."""

    def test_extract_returns_pending_claims(self, tmp_path):
        from llmxive.backends.dartmouth import DartmouthBackend
        from llmxive.claims.extract import extract_claims
        from llmxive.credentials import load_dartmouth_key

        key = load_dartmouth_key()
        if not key:
            pytest.skip("No Dartmouth key available")

        backend = DartmouthBackend()
        text = (
            "Knot theory studies closed loops in 3D space. "
            "There are 9,988 prime knots with at most 10 crossings "
            "(OEIS A002863, https://oeis.org/A002863). "
            "We use a convergence threshold of 0.95. "
            "The largest known prime knot has millions of crossings."
        )
        claims = extract_claims(
            text,
            artifact_path="test/doc.md",
            backend=backend,
            model="qwen.qwen3.5-122b",
            repo_root=tmp_path,
        )
        # Must return a list (possibly empty on extraction error)
        assert isinstance(claims, list)
        for c in claims:
            assert c.status == ClaimStatus.PENDING
            assert c.raw_text
            assert c.claim_id.startswith("c_")
        # Should NOT include the design threshold
        threshold_texts = [c.raw_text for c in claims if "0.95" in c.raw_text and "threshold" in c.raw_text.lower()]
        assert len(threshold_texts) == 0, f"Design threshold leaked into claims: {threshold_texts}"
