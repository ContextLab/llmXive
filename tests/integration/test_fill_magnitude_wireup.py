"""T021 — integration test: fill wire-in to resolve_magnitude.

Injects a real FillResult.filled("Jupiter", ...) at the fill_claim seam
(real object, NOT a mock backend) and asserts:
  - with LLMXIVE_CLAIM_FILL=1, a MAGNITUDE claim that would be NEI
    returns VERIFIED with value "Jupiter" and evidence.filled True.
  - with LLMXIVE_CLAIM_FILL unset, returns NEI unchanged.
"""

from __future__ import annotations

import pytest

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, Verdict, compute_claim_id
from llmxive.fill.models import FillProvenance, FillResult


# ---------------------------------------------------------------------------
# Real FillResult for Jupiter (largest planet)
# ---------------------------------------------------------------------------

_PROVENANCE = FillProvenance(
    value="Jupiter",
    source_id="Q319",
    url="https://www.wikidata.org/wiki/Q319",
    quote="Jupiter is the largest planet",
    channel="wikidata",
    conflicts=[],
)

_FILL_RESULT_FILLED = FillResult.filled("Jupiter", _PROVENANCE, ["wikidata"])


def _make_magnitude_claim(
    raw: str = "the largest planet is Saturn",
) -> Claim:
    kind = ClaimKind.MAGNITUDE
    cid = compute_claim_id(kind, raw, "test-context-magnitude-wireup")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=raw,
        canonical=raw,
        context="test-context-magnitude-wireup",
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

class TestFillMagnitudeWireup:

    def test_fill_flag_on_upgrades_nei_to_verified(self, monkeypatch, tmp_path):
        """With LLMXIVE_CLAIM_FILL=1, a MAGNITUDE NEI → VERIFIED via fill.

        The seam is fill_claim in fill.service — patched so the local import
        inside _maybe_fill sees the real FillResult.
        """
        import llmxive.fill.service as fill_service_mod
        import llmxive.claims.resolve as resolve_mod

        monkeypatch.setenv("LLMXIVE_CLAIM_FILL", "1")

        original = fill_service_mod.fill_claim
        fill_service_mod.fill_claim = lambda *a, **kw: _FILL_RESULT_FILLED
        try:
            claim = _make_magnitude_claim()
            nei = Verdict(
                status=ClaimStatus.NOT_ENOUGH_INFO,
                value=None,
                evidence={"reason": "no source found to validate superlative claim"},
                resolver="resolve_superlative",
            )
            result = resolve_mod._maybe_fill(
                claim, nei, backend=None, model=None, repo_root=tmp_path
            )
        finally:
            fill_service_mod.fill_claim = original

        assert result.status == ClaimStatus.VERIFIED
        assert result.value == "Jupiter"
        assert result.evidence is not None
        assert result.evidence.get("filled") is True
        fill_ev = result.evidence.get("fill", {})
        assert fill_ev.get("value") == "Jupiter"
        assert fill_ev.get("channel") == "wikidata"
        assert result.resolver == "fill:wikidata"

    def test_fill_flag_off_returns_nei_unchanged(self, monkeypatch, tmp_path):
        """Without LLMXIVE_CLAIM_FILL=1, _maybe_fill is a no-op for MAGNITUDE."""
        import llmxive.claims.resolve as resolve_mod

        monkeypatch.delenv("LLMXIVE_CLAIM_FILL", raising=False)

        claim = _make_magnitude_claim()
        nei = Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={"reason": "no source"},
            resolver="resolve_superlative",
        )
        result = resolve_mod._maybe_fill(
            claim, nei, backend=None, model=None, repo_root=tmp_path
        )
        assert result.status == ClaimStatus.NOT_ENOUGH_INFO
        assert result.value is None

    def test_fill_blocked_returns_original_verdict(self, monkeypatch, tmp_path):
        """If fill is blocked, the original NEI verdict is returned."""
        import llmxive.fill.service as fill_service_mod
        import llmxive.claims.resolve as resolve_mod

        blocked = FillResult.blocked("no candidate set found", ["wikidata", "wikipedia"])
        monkeypatch.setenv("LLMXIVE_CLAIM_FILL", "1")
        original = fill_service_mod.fill_claim
        fill_service_mod.fill_claim = lambda *a, **kw: blocked
        try:
            claim = _make_magnitude_claim()
            nei = Verdict(
                status=ClaimStatus.NOT_ENOUGH_INFO,
                value=None,
                evidence={"reason": "no source"},
                resolver="resolve_superlative",
            )
            result = resolve_mod._maybe_fill(
                claim, nei, backend=None, model=None, repo_root=tmp_path
            )
        finally:
            fill_service_mod.fill_claim = original
        assert result.status == ClaimStatus.NOT_ENOUGH_INFO

    def test_magnitude_kind_is_fillable(self):
        """MAGNITUDE must now be in _FILLABLE_KINDS (T020)."""
        from llmxive.fill.service import _FILLABLE_KINDS
        from llmxive.claims.models import ClaimKind
        assert ClaimKind.MAGNITUDE in _FILLABLE_KINDS

    def test_magnitude_channels_routed(self):
        """channels_for(MAGNITUDE) must return non-empty list (T020)."""
        from llmxive.fill.channels import channels_for
        from llmxive.claims.models import ClaimKind
        ch = channels_for(ClaimKind.MAGNITUDE, math=False)
        assert len(ch) > 0
        assert "wikidata" in ch or "wikipedia" in ch
