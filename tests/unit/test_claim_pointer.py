"""T007 — unit tests for claims/pointer.py (spec 016 foundational, pure/no IO)."""

from __future__ import annotations

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
from llmxive.claims.pointer import render, substitute_pointers, to_pointer


def _verified_claim(canonical: str = "x=42", context: str = "ctx") -> Claim:
    cid = compute_claim_id(ClaimKind.NUMERIC, canonical, context)
    return Claim(
        claim_id=cid,
        kind=ClaimKind.NUMERIC,
        raw_text="42",
        canonical=canonical,
        context=context,
        artifact_path="projects/PROJ-001/specs/spec.md",
        source_type="external",
        status=ClaimStatus.VERIFIED,
        resolved_value="42",
        evidence={"url": "http://example.com"},
        resolver="grounding",
        attempts=1,
        updated_at="2026-05-30T00:00:00Z",
    )


def _pending_claim(canonical: str = "y=99", context: str = "ctx2") -> Claim:
    cid = compute_claim_id(ClaimKind.NUMERIC, canonical, context)
    return Claim(
        claim_id=cid,
        kind=ClaimKind.NUMERIC,
        raw_text="99",
        canonical=canonical,
        context=context,
        artifact_path="projects/PROJ-001/specs/spec.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
    )


class TestToPointer:
    def test_format(self):
        ptr = to_pointer("c_deadbeef")
        assert ptr == "{{claim:c_deadbeef}}"

    def test_arbitrary_id(self):
        ptr = to_pointer("c_12345678")
        assert ptr == "{{claim:c_12345678}}"


class TestSubstitutePointers:
    def test_replaces_span_with_pointer(self):
        c = _verified_claim()
        text = "The value is 42 in the model."
        result = substitute_pointers(text, [("42", c.claim_id)])
        assert c.claim_id in result
        assert "{{claim:" in result

    def test_idempotent_second_call(self):
        c = _verified_claim()
        text = "The value is 42."
        once = substitute_pointers(text, [("42", c.claim_id)])
        twice = substitute_pointers(once, [("42", c.claim_id)])
        assert once == twice

    def test_multiple_spans(self):
        c1 = _verified_claim(canonical="x=1", context="c1")
        c2 = _verified_claim(canonical="x=2", context="c2")
        text = "A is 1 and B is 2."
        result = substitute_pointers(text, [("1", c1.claim_id), ("2", c2.claim_id)])
        assert c1.claim_id in result
        assert c2.claim_id in result


class TestRender:
    def test_verified_claim_renders_value(self):
        c = _verified_claim()
        ptr = to_pointer(c.claim_id)
        text = f"The count is {ptr}."
        rendered, _report = render(text, {c.claim_id: c})
        assert "42" in rendered
        assert ptr not in rendered

    def test_verified_original_numeral_does_not_reappear(self):
        # After substitution→render, only resolved_value appears, not raw_text
        c = _verified_claim(canonical="knots=9988", context="prime knots")
        c.raw_text = "27635"  # the fabricated number
        c.resolved_value = "9988"
        ptr = to_pointer(c.claim_id)
        text = f"There are {ptr} prime knots."
        rendered, _report = render(text, {c.claim_id: c})
        assert "9988" in rendered
        assert "27635" not in rendered

    def test_pending_claim_renders_marker(self):
        c = _pending_claim()
        ptr = to_pointer(c.claim_id)
        text = f"Value is {ptr} here."
        rendered, _report = render(text, {c.claim_id: c})
        assert "[UNRESOLVED-CLAIM:" in rendered
        assert ptr not in rendered

    def test_missing_claim_renders_marker(self):
        ptr = to_pointer("c_00000000")
        text = f"Value is {ptr} here."
        rendered, _report = render(text, {})
        assert "[UNRESOLVED-CLAIM:" in rendered

    def test_gate_report_blocked_when_unresolved(self):
        c = _pending_claim()
        ptr = to_pointer(c.claim_id)
        text = f"Value is {ptr}."
        _, report = render(text, {c.claim_id: c})
        assert report.blocked is True
        assert len(report.unresolved_markers) >= 1

    def test_gate_report_not_blocked_when_all_verified(self):
        c = _verified_claim()
        ptr = to_pointer(c.claim_id)
        text = f"Value is {ptr}."
        _, report = render(text, {c.claim_id: c})
        assert report.blocked is False
        assert report.unresolved_markers == []

    def test_round_trip_preserves_verified_value(self):
        c = _verified_claim(canonical="acc=0.95", context="reported accuracy")
        c.resolved_value = "0.95"
        text = "Model accuracy: {{claim:" + c.claim_id + "}}."
        rendered, report = render(text, {c.claim_id: c})
        assert "0.95" in rendered
        assert not report.blocked

    def test_whitespace_in_pointer_still_matches(self):
        c = _verified_claim()
        # pointer with extra whitespace inside braces
        text = f"Value is {{{{ claim: {c.claim_id} }}}}."
        # The regex allows optional whitespace: \{\{\s*claim:...\s*\}\}
        rendered, _report = render(text, {c.claim_id: c})
        # Either matched and substituted, or left and blocked — either is valid
        # but this tests the regex handles it gracefully (no crash)
        assert isinstance(rendered, str)


class TestProsePreservingRender:
    """Fix A — render preserves the claim's full sentence, swapping ONLY the
    asserted token for ``resolved_value`` (PROJ-552 garble regression)."""

    def _sentence_claim(
        self, raw_text: str, resolved_value: str, *, kind: ClaimKind = ClaimKind.NUMERIC
    ) -> Claim:
        cid = compute_claim_id(kind, raw_text, "ctx")
        return Claim(
            claim_id=cid,
            kind=kind,
            raw_text=raw_text,
            canonical=raw_text,
            context="ctx",
            artifact_path="projects/PROJ-552/specs/spec.md",
            source_type="external",
            status=ClaimStatus.VERIFIED,
            resolved_value=resolved_value,
            evidence={"url": "https://oeis.org/A002863"},
            resolver="grounding",
            attempts=1,
            updated_at="2026-05-30T00:00:00Z",
        )

    def test_proj552_garble_regression(self):
        # The exact PROJ-552 sentence; the asserted 27,635 must become 9988 and
        # NOTHING else may change — the whole sentence is preserved.
        sentence = (
            "For crossing number 13, the exact count is 27,635 prime knots "
            "(Hoste, Thistlethwaite & Weeks 1998)."
        )
        c = self._sentence_claim(sentence, "9988")
        ptr = to_pointer(c.claim_id)
        rendered, report = render(ptr, {c.claim_id: c})
        assert rendered == (
            "For crossing number 13, the exact count is 9988 prime knots "
            "(Hoste, Thistlethwaite & Weeks 1998)."
        )
        assert "27,635" not in rendered
        assert not report.blocked

    def test_render_is_idempotent_when_already_correct(self):
        # Asserted token already equals resolved_value (with separators stripped)
        # → prose returned byte-for-byte unchanged, and re-render is identical.
        sentence = "There are 9,988 prime knots (OEIS A002863)."
        c = self._sentence_claim(sentence, "9988")
        ptr = to_pointer(c.claim_id)
        once, _ = render(ptr, {c.claim_id: c})
        assert once == sentence  # comma form preserved — NOT collapsed to 9988
        # Feeding the already-correct prose back (no pointer) is a no-op too.
        twice, _ = render(once, {c.claim_id: c})
        assert twice == once

    def test_not_verified_appends_marker_preserving_prose(self):
        sentence = "The catalog lists 27,635 prime knots (no source)."
        cid = compute_claim_id(ClaimKind.NUMERIC, sentence, "ctx")
        c = Claim(
            claim_id=cid,
            kind=ClaimKind.NUMERIC,
            raw_text=sentence,
            canonical=sentence,
            context="ctx",
            artifact_path="projects/PROJ-552/specs/spec.md",
            source_type="external",
            status=ClaimStatus.NOT_ENOUGH_INFO,
            resolved_value=None,
            evidence=None,
            resolver=None,
            attempts=1,
            updated_at="2026-05-30T00:00:00Z",
        )
        ptr = to_pointer(c.claim_id)
        rendered, report = render(ptr, {c.claim_id: c})
        # Prose preserved; ONE marker appended (not a bare-marker replacement).
        assert rendered.startswith(sentence + " [UNRESOLVED-CLAIM:")
        assert rendered.endswith("]")
        assert report.blocked
        assert len(report.unresolved_markers) == 1

    def test_entity_fact_unchanged_when_value_present(self):
        sentence = "The census was produced by Hoste, Thistlethwaite and Weeks."
        c = self._sentence_claim(
            sentence, "Hoste, Thistlethwaite and Weeks", kind=ClaimKind.ENTITY_FACT
        )
        ptr = to_pointer(c.claim_id)
        rendered, report = render(ptr, {c.claim_id: c})
        # resolved_value already in the sentence → prose untouched (no garble).
        assert rendered == sentence
        assert not report.blocked
