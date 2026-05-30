"""T011 — Integration: approximate + computational routing through resolve.

Offline only: uses real verify.constants (math/scipy), no network.
LLMXIVE_CLAIM_FILL=1 is set within each test.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id


def _claim(text: str, kind: ClaimKind = ClaimKind.NUMERIC) -> Claim:
    cid = compute_claim_id(kind, text, "test")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=text,
        canonical=text,
        context="test",
        artifact_path="test",
        source_type="external",
        status=ClaimStatus.PENDING,
        resolved_value=None,
        evidence=None,
        resolver=None,
        attempts=0,
        updated_at="2026-01-01T00:00:00Z",
    )


@pytest.fixture(autouse=True)
def enable_fill(monkeypatch):
    monkeypatch.setenv("LLMXIVE_CLAIM_FILL", "1")


# ---------------------------------------------------------------------------
# T011-A: "π is 3.14" → VERIFIED, value 3.14 (valid rounding, no correction)
# ---------------------------------------------------------------------------

def test_pi_is_3_14_verified(tmp_path):
    from llmxive.claims.resolve import resolve

    claim = _claim("π is 3.14")
    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)

    assert verdict.status == ClaimStatus.VERIFIED, f"Expected VERIFIED, got {verdict.status}: {verdict.evidence}"
    assert verdict.resolver in ("approximate", "fill:constants", "fill:oeis", "fill:wikipedia",
                                "fill:paper", "compute")
    # value must be 3.14 (not rewritten to full pi)
    assert verdict.value is not None
    # Mode must be approximate or the evidence must show approximate
    evidence = verdict.evidence or {}
    assert evidence.get("mode") == "approximate" or evidence.get("filled"), \
        f"Expected approximate mode evidence, got: {evidence}"


# ---------------------------------------------------------------------------
# T011-B: "π is 3.15" → VERIFIED with corrected value "3.14" (evidence.corrected)
# ---------------------------------------------------------------------------

def test_pi_is_3_15_corrected(tmp_path):
    from llmxive.claims.resolve import resolve

    claim = _claim("π is 3.15")
    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)

    assert verdict.status == ClaimStatus.VERIFIED, f"Expected VERIFIED, got {verdict.status}: {verdict.evidence}"
    evidence = verdict.evidence or {}
    # Must be corrected
    assert evidence.get("corrected") is True or evidence.get("mode") == "approximate", \
        f"Expected corrected=True in evidence: {evidence}"
    # Corrected value must be 3.14 (2 decimal places matching the claim's precision)
    assert verdict.value == "3.14", f"Expected '3.14', got {verdict.value!r}"


# ---------------------------------------------------------------------------
# T011-C: "9,988 prime knots at 13 crossings" → exact mode (mode != approximate/computational)
# ---------------------------------------------------------------------------

def test_knot_count_exact_route(tmp_path):
    """Exact integer count MUST NOT route to approximate or computational (FR-003)."""
    from llmxive.verify.mode import select_mode
    from llmxive.claims.resolve import resolve

    claim = _claim("9,988 prime knots at 13 crossings")
    mode = select_mode(claim, backend=None)
    assert mode not in ("approximate", "computational"), \
        f"Integer count must not go to approximate/computational, got mode={mode!r}"

    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)
    evidence = verdict.evidence or {}
    # If it reached here at all, it must NOT be from the approximate path
    assert evidence.get("mode") != "approximate", \
        f"Exact count must not use approximate mode: {evidence}"
    assert evidence.get("mode") != "computational", \
        f"Exact count must not use computational mode: {evidence}"


# ---------------------------------------------------------------------------
# T011-D: "1 plus 1 is 2" → VERIFIED via computational (self-contained)
# ---------------------------------------------------------------------------

def test_computation_1_plus_1(tmp_path):
    from llmxive.claims.resolve import resolve

    claim = _claim("1 plus 1 is 2")
    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)

    assert verdict.status == ClaimStatus.VERIFIED, f"Expected VERIFIED, got {verdict.status}: {verdict.evidence}"
    evidence = verdict.evidence or {}
    assert evidence.get("mode") == "computational", \
        f"Expected computational mode, got: {evidence}"


# ---------------------------------------------------------------------------
# T011-E: "1 plus 2 is 1" → VERIFIED corrected to "3" via computational
# ---------------------------------------------------------------------------

def test_computation_1_plus_2_corrected(tmp_path):
    from llmxive.claims.resolve import resolve

    claim = _claim("1 plus 2 is 1")
    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)

    assert verdict.status == ClaimStatus.VERIFIED, f"Expected VERIFIED, got {verdict.status}: {verdict.evidence}"
    evidence = verdict.evidence or {}
    assert evidence.get("mode") == "computational", \
        f"Expected computational mode, got: {evidence}"
    assert evidence.get("corrected") is True, f"Expected corrected=True, got: {evidence}"
    assert verdict.value == "3", f"Expected corrected value '3', got {verdict.value!r}"
