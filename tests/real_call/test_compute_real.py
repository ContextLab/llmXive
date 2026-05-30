"""T019 — Real-call: computational mode via resolve (gated LLMXIVE_REAL_TESTS).

The evaluation is deterministic (sympy, no LLM needed with backend=None).
Assert the computed value came from sympy (evidence.compute.computed), not the model.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="set LLMXIVE_REAL_TESTS=1 to run real-call tests",
)

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id


def _claim(text: str, kind: ClaimKind = ClaimKind.NUMERIC) -> Claim:
    cid = compute_claim_id(kind, text, "test-compute")
    return Claim(
        claim_id=cid,
        kind=kind,
        raw_text=text,
        canonical=text,
        context="test-compute",
        artifact_path="test-compute",
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
# T019-A: "1 plus 1 is 2" → VERIFIED computational
# ---------------------------------------------------------------------------

def test_1_plus_1_is_2(tmp_path):
    from llmxive.claims.resolve import resolve

    claim = _claim("1 plus 1 is 2")
    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)

    assert verdict.status == ClaimStatus.VERIFIED
    evidence = verdict.evidence or {}
    assert evidence.get("mode") == "computational"
    assert "compute" in evidence
    compute = evidence["compute"]
    # Value came from sympy, not LLM
    assert "computed" in compute
    assert compute["computed"] == "2"
    assert compute.get("expression") is not None
    assert verdict.resolver == "compute"


# ---------------------------------------------------------------------------
# T019-B: "1 plus 2 is 1" → VERIFIED corrected to "3" (evidence.corrected)
# ---------------------------------------------------------------------------

def test_1_plus_2_is_1_corrected(tmp_path):
    from llmxive.claims.resolve import resolve

    claim = _claim("1 plus 2 is 1")
    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)

    assert verdict.status == ClaimStatus.VERIFIED
    evidence = verdict.evidence or {}
    assert evidence.get("mode") == "computational"
    assert evidence.get("corrected") is True
    # Correct value is 3
    assert verdict.value == "3", f"Expected '3', got {verdict.value!r}"
    compute = evidence.get("compute", {})
    assert compute.get("computed") == "3"


# ---------------------------------------------------------------------------
# T019-C: "1 is larger than 2" → VERIFIED corrected (False, not True)
# ---------------------------------------------------------------------------

def test_1_larger_than_2_refuted(tmp_path):
    from llmxive.claims.resolve import resolve

    claim = _claim("1 is larger than 2")
    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)

    assert verdict.status == ClaimStatus.VERIFIED
    evidence = verdict.evidence or {}
    assert evidence.get("mode") == "computational"
    # The claim "1 > 2" is False, so it should be corrected
    assert evidence.get("corrected") is True
    compute = evidence.get("compute", {})
    assert compute.get("computed") == "False"


# ---------------------------------------------------------------------------
# T019-D: "30% of 200 is 60" → VERIFIED
# ---------------------------------------------------------------------------

def test_30pct_of_200_is_60(tmp_path):
    from llmxive.claims.resolve import resolve

    claim = _claim("30% of 200 is 60")
    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)

    assert verdict.status == ClaimStatus.VERIFIED
    evidence = verdict.evidence or {}
    assert evidence.get("mode") == "computational"
    assert verdict.resolver == "compute"
    compute = evidence.get("compute", {})
    assert compute.get("computed") == "60"


# ---------------------------------------------------------------------------
# T019-E: "5 km is 5,200 m" → corrected to ~5000
# ---------------------------------------------------------------------------

def test_5km_5200m_corrected(tmp_path):
    from llmxive.claims.resolve import resolve

    claim = _claim("5 km is 5,200 m")
    verdict = resolve(claim, backend=None, model=None, repo_root=tmp_path)

    assert verdict.status == ClaimStatus.VERIFIED
    evidence = verdict.evidence or {}
    assert evidence.get("mode") == "computational"
    assert evidence.get("corrected") is True
    compute = evidence.get("compute", {})
    # Computed value should be 5000 (5 km = 5000 m)
    computed_str = compute.get("computed", "")
    # Accept "5000" or "5000.0" or sympy rational form
    assert "5000" in computed_str, f"Expected 5000 in computed: {computed_str!r}"
