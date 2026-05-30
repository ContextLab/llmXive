"""T020 — integration test: fill wire-in to resolve_numeric_or_citation.

Injects a real FillResult.filled(...) at the fill_claim seam (no mock backend,
no mock channels — the injected value is a real FillResult object) and asserts:
  - with LLMXIVE_CLAIM_FILL=1, a numeric claim that would resolve to NEI
    returns VERIFIED with value "9988" and evidence.filled True.
  - with LLMXIVE_CLAIM_FILL unset (or "0"), returns NEI unchanged.
"""

from __future__ import annotations

import importlib
import pytest

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, Verdict, compute_claim_id
from llmxive.fill.models import FillProvenance, FillResult


# ---------------------------------------------------------------------------
# Helper: a real FillResult.filled for A002863 / 9988
# ---------------------------------------------------------------------------

_PROVENANCE = FillProvenance(
    value="9988",
    source_id="A002863",
    url="https://oeis.org/A002863",
    quote="13 9988",
    channel="oeis",
    conflicts=[],
)

_FILL_RESULT_FILLED = FillResult.filled("9988", _PROVENANCE, ["oeis"])


def _make_numeric_claim(raw: str = "there are 27635 prime knots at 13 crossings") -> Claim:
    kind = ClaimKind.NUMERIC
    cid = compute_claim_id(kind, raw, "test-context-wireup")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=raw,
        canonical=raw,
        context="test-context-wireup",
        artifact_path="projects/PROJ-552/idea/foo.md",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value="27635",
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-05-30T00:00:00Z",
    )


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------

class TestFillWireup:

    def test_fill_flag_on_upgrades_nei_to_verified(self, monkeypatch, tmp_path):
        """With LLMXIVE_CLAIM_FILL=1, NEI → VERIFIED via fill.

        _maybe_fill does `from llmxive.fill.service import fill_claim` as a local
        import.  We patch the function at its definition site inside the module
        namespace so the local import sees the patched version.
        """
        import llmxive.fill.service as fill_service_mod
        import llmxive.claims.resolve as resolve_mod

        monkeypatch.setenv("LLMXIVE_CLAIM_FILL", "1")

        # Replace fill_claim in the fill.service module namespace so the
        # `from llmxive.fill.service import fill_claim` inside _maybe_fill
        # resolves to our injected function.
        original = fill_service_mod.fill_claim
        fill_service_mod.fill_claim = lambda *a, **kw: _FILL_RESULT_FILLED
        try:
            claim = _make_numeric_claim()
            nei = Verdict(
                status=ClaimStatus.NOT_ENOUGH_INFO,
                value=None,
                evidence={"reason": "no resolvable source"},
                resolver="resolve_numeric_or_citation",
            )
            result = resolve_mod._maybe_fill(claim, nei, backend=None, model=None,
                                             repo_root=tmp_path)
        finally:
            fill_service_mod.fill_claim = original

        assert result.status == ClaimStatus.VERIFIED
        assert result.value == "9988"
        assert result.evidence is not None
        assert result.evidence.get("filled") is True
        fill_ev = result.evidence.get("fill", {})
        assert fill_ev.get("value") == "9988"
        assert fill_ev.get("channel") == "oeis"
        assert result.resolver == "fill:oeis"

    def test_fill_flag_off_returns_nei_unchanged(self, monkeypatch, tmp_path):
        """Without LLMXIVE_CLAIM_FILL=1, _maybe_fill is a no-op."""
        import llmxive.claims.resolve as resolve_mod

        monkeypatch.delenv("LLMXIVE_CLAIM_FILL", raising=False)

        claim = _make_numeric_claim()
        nei = Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={"reason": "no source"},
            resolver="resolve_numeric_or_citation",
        )
        result = resolve_mod._maybe_fill(claim, nei, backend=None, model=None,
                                         repo_root=tmp_path)
        assert result.status == ClaimStatus.NOT_ENOUGH_INFO
        assert result.value is None

    def test_fill_flag_zero_returns_nei_unchanged(self, monkeypatch, tmp_path):
        """LLMXIVE_CLAIM_FILL=0 is treated as flag-off."""
        import llmxive.claims.resolve as resolve_mod

        monkeypatch.setenv("LLMXIVE_CLAIM_FILL", "0")

        claim = _make_numeric_claim()
        nei = Verdict(
            status=ClaimStatus.NOT_ENOUGH_INFO,
            value=None,
            evidence={"reason": "no source"},
            resolver="resolve_numeric_or_citation",
        )
        result = resolve_mod._maybe_fill(claim, nei, backend=None, model=None,
                                         repo_root=tmp_path)
        assert result.status == ClaimStatus.NOT_ENOUGH_INFO

    def test_result_kind_never_filled(self, monkeypatch, tmp_path):
        """RESULT claims must not be upgraded even when LLMXIVE_CLAIM_FILL=1."""
        import llmxive.fill.service as fill_service_mod
        import llmxive.claims.resolve as resolve_mod

        monkeypatch.setenv("LLMXIVE_CLAIM_FILL", "1")
        original = fill_service_mod.fill_claim
        fill_service_mod.fill_claim = lambda *a, **kw: _FILL_RESULT_FILLED
        try:
            cid = compute_claim_id(ClaimKind.RESULT, "result:42", "ctx")
            result_claim = Claim(
                claim_id=cid,
                kind=ClaimKind.RESULT,
                raw_text="result: 42",
                canonical="result:42",
                context="ctx",
                artifact_path="projects/PROJ-001/foo.md",
                source_type="result",
                status=ClaimStatus.PENDING,
                resolved_value=None,
                evidence=None,
                resolver=None,
                attempts=0,
                updated_at="2026-05-30T00:00:00Z",
            )
            nei = Verdict(
                status=ClaimStatus.NOT_ENOUGH_INFO,
                value=None,
                evidence={"reason": "no receipt"},
                resolver="resolve_result",
            )
            result = resolve_mod._maybe_fill(result_claim, nei, backend=None, model=None,
                                             repo_root=tmp_path)
        finally:
            fill_service_mod.fill_claim = original
        assert result.status == ClaimStatus.NOT_ENOUGH_INFO

    def test_fill_blocked_returns_original(self, monkeypatch, tmp_path):
        """If fill returns blocked, the original verdict is returned unchanged."""
        import llmxive.fill.service as fill_service_mod
        import llmxive.claims.resolve as resolve_mod

        blocked = FillResult.blocked("no source found", ["oeis", "wikipedia"])
        monkeypatch.setenv("LLMXIVE_CLAIM_FILL", "1")
        original = fill_service_mod.fill_claim
        fill_service_mod.fill_claim = lambda *a, **kw: blocked
        try:
            claim = _make_numeric_claim()
            nei = Verdict(
                status=ClaimStatus.NOT_ENOUGH_INFO,
                value=None,
                evidence={"reason": "no source"},
                resolver="resolve_numeric_or_citation",
            )
            result = resolve_mod._maybe_fill(claim, nei, backend=None, model=None,
                                             repo_root=tmp_path)
        finally:
            fill_service_mod.fill_claim = original
        assert result.status == ClaimStatus.NOT_ENOUGH_INFO
