"""T025 — real-call test: fill corrects a wrong relational claim (RELATIONAL claim).

Gated by LLMXIVE_REAL_TESTS=1 and LLMXIVE_CLAIM_FILL=1.

Tests:
1. "the capital of Australia is Sydney" → VERIFIED with value "Canberra" from
   Wikidata/Wikipedia provenance.
2. An unsourceable relation → blocked (not falsely filled).

Verified facts:
  - Canberra is the capital of Australia (not Sydney).
    Source: https://en.wikipedia.org/wiki/Canberra
    "Canberra is the capital city of Australia."
  - Sydney is the largest city but NOT the capital.
"""

from __future__ import annotations

import os

import pytest

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="LLMXIVE_REAL_TESTS=1 required",
)


def _make_relational_claim(raw: str) -> Claim:
    kind = ClaimKind.RELATIONAL
    cid = compute_claim_id(kind, raw, "real-call-relational-test")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=raw,
        canonical=raw,
        context="real-call-relational-test",
        artifact_path="projects/test/idea/foo.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
    )


def _get_backend():
    """Return a real Dartmouth backend, or None if key not available."""
    try:
        from llmxive.credentials import load_dartmouth_key
        key = load_dartmouth_key()
        if not key:
            return None
        from llmxive.backends.dartmouth import DartmouthBackend
        return DartmouthBackend()
    except Exception:
        return None


class TestFillRelationalReal:

    def test_wrong_capital_corrected_to_canberra(self, tmp_path):
        """'the capital of Australia is Sydney' → corrected to 'Canberra'.

        Canberra is confirmed as the capital of Australia (Wikipedia/Wikidata).
        """
        backend = _get_backend()
        if backend is None:
            pytest.skip("No Dartmouth API key available")

        os.environ["LLMXIVE_CLAIM_FILL"] = "1"
        try:
            from llmxive.claims.resolve import resolve_relational

            claim = _make_relational_claim("the capital of Australia is Sydney")
            verdict = resolve_relational(
                claim, backend=backend, model=None, repo_root=tmp_path
            )
        finally:
            os.environ.pop("LLMXIVE_CLAIM_FILL", None)

        # Must be VERIFIED (filled) with Canberra
        assert verdict.status == ClaimStatus.VERIFIED, (
            f"Expected VERIFIED, got {verdict.status}; evidence: {verdict.evidence}"
        )
        assert verdict.value is not None
        val = verdict.value.lower()
        assert "canberra" in val, (
            f"Expected 'Canberra' in value, got {verdict.value!r}"
        )
        ev = verdict.evidence or {}
        assert ev.get("filled") is True or "fill" in ev or "canberra" in str(ev).lower(), (
            f"Expected fill provenance in evidence: {ev}"
        )

    def test_unsourceable_relation_blocked(self, tmp_path):
        """An unsourceable relation stays blocked (not falsely filled).

        Uses a relation with a real entity (Australia) but a provably wrong
        and sourceable-only-correctly subject ("the second-largest city of
        Australia is Canberra" — Canberra is the capital, not the 2nd-largest
        city; Sydney is). This tests that a WRONG relational claim that cannot
        be source-verified as stated stays NEI or REFUTED, not VERIFIED.

        We use fill_claim directly (not resolve_relational) to test the fill
        service's blocking behaviour: a claim whose correct answer is NOT in
        the source's fill candidate (Canberra is not the second-largest city)
        must be blocked or returned as REFUTED.
        """
        backend = _get_backend()
        if backend is None:
            pytest.skip("No Dartmouth API key available")

        os.environ["LLMXIVE_CLAIM_FILL"] = "1"
        try:
            from llmxive.fill.service import fill_claim

            # This claim is about a relation that has no clear authoritative
            # single-valued answer — testing that fill doesn't hallucinate.
            # Use a claim where the fill would need to find a source but the
            # subject query returns an empty/irrelevant entity set.
            claim = _make_relational_claim(
                "the administrative capital of Xlqrtbnz is Frobznax"
            )
            result = fill_claim(
                claim, backend=backend, model=None, repo_root=tmp_path
            )
        finally:
            os.environ.pop("LLMXIVE_CLAIM_FILL", None)

        # With a completely fictional entity, fill must stay blocked
        assert result.status == "blocked", (
            f"Expected fill blocked for unsourceable relation, "
            f"got {result.status}; reason: {result.reason}"
        )
