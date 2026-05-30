"""T024 — integration test: fill wire-in to resolve_relational.

Injects a real FillResult.filled("Canberra", ...) at the fill_claim seam
(real object, NOT a mock backend) and asserts:
  - with LLMXIVE_CLAIM_FILL=1, a RELATIONAL claim that would be NEI/REFUTED
    returns VERIFIED with the corrected object + evidence.filled.
  - multi-valued-relation case: claimed object present in source → VERIFIED
    (fill returns the claimed object without over-correcting).
  - with LLMXIVE_CLAIM_FILL unset, returns NEI unchanged.
"""

from __future__ import annotations

import pytest

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, Verdict, compute_claim_id
from llmxive.fill.models import FillProvenance, FillResult


# ---------------------------------------------------------------------------
# Real FillResult objects
# ---------------------------------------------------------------------------

_PROV_CANBERRA = FillProvenance(
    value="Canberra",
    source_id="Q3114",
    url="https://www.wikidata.org/wiki/Q3114",
    quote="Canberra is the capital of Australia",
    channel="wikidata",
    conflicts=[],
)
_FILL_CANBERRA = FillResult.filled("Canberra", _PROV_CANBERRA, ["wikidata"])

# Multi-valued case: the claimed object IS one of the valid objects (e.g.
# English is one of several official languages of a country).
_PROV_ENGLISH = FillProvenance(
    value="English",
    source_id="Q7979",
    url="https://www.wikidata.org/wiki/Q7979",
    quote="English is an official language of Australia",
    channel="wikidata",
    conflicts=[],
)
_FILL_ENGLISH = FillResult.filled("English", _PROV_ENGLISH, ["wikidata"])


def _make_relational_claim(
    raw: str = "the capital of Australia is Sydney",
) -> Claim:
    kind = ClaimKind.RELATIONAL
    cid = compute_claim_id(kind, raw, "test-context-relational-wireup")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=raw,
        canonical=raw,
        context="test-context-relational-wireup",
        artifact_path="projects/PROJ-552/idea/foo.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFillRelationalWireup:

    def test_fill_flag_on_upgrades_nei_to_verified(self, monkeypatch, tmp_path):
        """With LLMXIVE_CLAIM_FILL=1, a RELATIONAL NEI → VERIFIED with Canberra."""
        import llmxive.fill.service as fill_service_mod
        import llmxive.claims.resolve as resolve_mod

        monkeypatch.setenv("LLMXIVE_CLAIM_FILL", "1")

        original = fill_service_mod.fill_claim
        fill_service_mod.fill_claim = lambda *a, **kw: _FILL_CANBERRA
        try:
            claim = _make_relational_claim()
            nei = Verdict(
                status=ClaimStatus.NOT_ENOUGH_INFO,
                value=None,
                evidence={"reason": "no citable source found for relational claim"},
                resolver="resolve_relational",
            )
            result = resolve_mod._maybe_fill(
                claim, nei, backend=None, model=None, repo_root=tmp_path
            )
        finally:
            fill_service_mod.fill_claim = original

        assert result.status == ClaimStatus.VERIFIED
        assert result.value == "Canberra"
        assert result.evidence is not None
        assert result.evidence.get("filled") is True
        fill_ev = result.evidence.get("fill", {})
        assert fill_ev.get("value") == "Canberra"
        assert fill_ev.get("channel") == "wikidata"
        assert result.resolver == "fill:wikidata"

    def test_fill_flag_off_returns_nei_unchanged(self, monkeypatch, tmp_path):
        """Without LLMXIVE_CLAIM_FILL=1, _maybe_fill is a no-op for RELATIONAL."""
        import llmxive.claims.resolve as resolve_mod

        monkeypatch.delenv("LLMXIVE_CLAIM_FILL", raising=False)

        claim = _make_relational_claim()
        nei = Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={"reason": "no source"},
            resolver="resolve_relational",
        )
        result = resolve_mod._maybe_fill(
            claim, nei, backend=None, model=None, repo_root=tmp_path
        )
        assert result.status == ClaimStatus.NOT_ENOUGH_INFO
        assert result.value is None

    def test_multivalued_relation_claimed_object_verified(self, monkeypatch, tmp_path):
        """FR-009: a claimed object that IS present in the source set is VERIFIED.

        The fill service returns "English" (the claimed object) for a language
        claim; the result should be VERIFIED, not over-corrected to a different
        language.
        """
        import llmxive.fill.service as fill_service_mod
        import llmxive.claims.resolve as resolve_mod

        monkeypatch.setenv("LLMXIVE_CLAIM_FILL", "1")

        # Fill returns the same value as the claim asserted
        original = fill_service_mod.fill_claim
        fill_service_mod.fill_claim = lambda *a, **kw: _FILL_ENGLISH
        try:
            claim = _make_relational_claim(
                raw="the official language of Australia is English"
            )
            nei = Verdict(
                status=ClaimStatus.NOT_ENOUGH_INFO,
                value=None,
                evidence={"reason": "source found but does not address relational claim"},
                resolver="resolve_relational",
            )
            result = resolve_mod._maybe_fill(
                claim, nei, backend=None, model=None, repo_root=tmp_path
            )
        finally:
            fill_service_mod.fill_claim = original

        # The fill returned "English" (the claimed object is valid) → VERIFIED
        assert result.status == ClaimStatus.VERIFIED
        assert result.value == "English"
        assert result.evidence.get("filled") is True

    def test_fill_blocked_returns_original_verdict(self, monkeypatch, tmp_path):
        """If fill is blocked, the original NEI verdict is returned."""
        import llmxive.fill.service as fill_service_mod
        import llmxive.claims.resolve as resolve_mod

        blocked = FillResult.blocked("no authoritative source", ["wikidata", "wikipedia"])
        monkeypatch.setenv("LLMXIVE_CLAIM_FILL", "1")
        original = fill_service_mod.fill_claim
        fill_service_mod.fill_claim = lambda *a, **kw: blocked
        try:
            claim = _make_relational_claim()
            nei = Verdict(
                status=ClaimStatus.NOT_ENOUGH_INFO,
                value=None,
                evidence={"reason": "no source"},
                resolver="resolve_relational",
            )
            result = resolve_mod._maybe_fill(
                claim, nei, backend=None, model=None, repo_root=tmp_path
            )
        finally:
            fill_service_mod.fill_claim = original
        assert result.status == ClaimStatus.NOT_ENOUGH_INFO

    def test_relational_kind_is_fillable(self):
        """RELATIONAL must now be in _FILLABLE_KINDS (T023)."""
        from llmxive.fill.service import _FILLABLE_KINDS
        from llmxive.claims.models import ClaimKind
        assert ClaimKind.RELATIONAL in _FILLABLE_KINDS

    def test_relational_channels_routed(self):
        """channels_for(RELATIONAL) must return non-empty list (T023)."""
        from llmxive.fill.channels import channels_for
        from llmxive.claims.models import ClaimKind
        ch = channels_for(ClaimKind.RELATIONAL, math=False)
        assert len(ch) > 0
        assert "wikidata" in ch or "wikipedia" in ch
