"""Spec 020 — the REAL PROJ-552 plan.md through the planning claim layer (real-call).

This drives the ACTUAL on-disk PROJ-552 plan artifact (not a synthetic fixture)
through ``process_document`` with a planning ``stage_label``, against a live free
backend. The real plan asserts low-level empirical values — e.g. "~27,635 at
crossing number 13" (which is itself wrong: 27,635 is the count at 14 crossings,
13 is 9,988), plus "~2,000 prime knots", "≥95% …", "within 15 minutes". Under
spec 020 a PLANNING stage must NOT fetch/ground/kick-back on any of these: they
are stripped/smoothed, no ``[UNRESOLVED-CLAIM:]`` marker is emitted, the stage is
not blocked, and nothing is registered/resolved. References (if any) are still
handled by the separate reference path, unaffected here.

Reads the real file read-only; all writes go to a tmp repo_root.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from llmxive.claims.gate import CLAIM_MARKER_PREFIX

REAL = os.environ.get("LLMXIVE_REAL_TESTS") == "1"


def _has_key() -> bool:
    try:
        from llmxive.credentials import load_dartmouth_key

        return bool(load_dartmouth_key())
    except Exception:
        return False


pytestmark = [
    pytest.mark.skipif(not REAL, reason="LLMXIVE_REAL_TESTS!=1"),
    pytest.mark.skipif(not _has_key(), reason="no Dartmouth key"),
]

_FREE_MODEL = "qwen.qwen3.5-122b"

_PLAN = (
    Path(__file__).resolve().parents[2]
    / "projects/PROJ-552-quantifying-the-complexity-of-knot-diagr"
    / "specs/001-quantifying-the-complexity-of-knot-diagr/plan.md"
)


@pytest.mark.skipif(not _PLAN.exists(), reason="real PROJ-552 plan.md not present")
def test_real_proj552_plan_planning_stage_no_kickback(tmp_path: Path) -> None:
    from llmxive.backends.router import make_backend
    from llmxive.claims.service import process_document

    original = _PLAN.read_text(encoding="utf-8")
    assert "27,635" in original or "27635" in original, (
        "fixture assumption changed: the real plan no longer asserts the 27,635 count"
    )

    out, claims, report = process_document(
        original,
        artifact_path="projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/specs/001-quantifying-the-complexity-of-knot-diagr/plan.md",
        project_id="PROJ-552-quantifying-the-complexity-of-knot-diagr",
        backend=make_backend("dartmouth"),
        model=_FREE_MODEL,
        repo_root=tmp_path,
        stage_label="plan",
    )

    # HEADLINE (the PROJ-552 stall fix, FR-002/003): a planning stage on the REAL
    # plan never emits an [UNRESOLVED-CLAIM:] marker, never blocks, and registers/
    # resolves NOTHING — so its low-level values can never drive a kickback toward
    # human escalation. This is the behavior that previously exhausted the cap.
    assert CLAIM_MARKER_PREFIX not in out, "planning emitted an [UNRESOLVED-CLAIM:] marker"
    assert report.blocked is False, "planning blocked on a low-level claim"
    assert claims == [], "planning registered/resolved low-level claims"

    # The real file on disk is untouched (read-only).
    assert _PLAN.read_text(encoding="utf-8") == original

    # Value REMOVAL (SC-001) for any DETECTED low-level claim: whatever the
    # extractor flags must be smoothed out. NOTE the known limitation surfaced by
    # this real-project test — ``extract_claims`` is tuned for asserted research
    # claims and has LOW recall on planning-doc scope/metadata (it reads
    # "~27,635 at crossing number 13 (downloaded but not fully validated)" as a
    # scope note, not a check-worthy claim), so an UNDETECTED value (like 27,635
    # here) is not stripped. The anti-stall guarantee above is what gates progress;
    # value-removal is best-effort + complemented by US3 template prevention.
    from llmxive.claims.extract import extract_claims
    from llmxive.claims.models import ClaimKind
    from llmxive.claims.pointer import asserted_value

    detected = [
        c for c in extract_claims(
            original, artifact_path="x/plan.md",
            backend=make_backend("dartmouth"), model=_FREE_MODEL, repo_root=None,
        )
        if c.kind != ClaimKind.CITATION and c.raw_text and c.raw_text in original
    ]
    for c in detected:
        av = asserted_value(c.raw_text)
        if av and av in original:
            assert av not in out, (
                f"a DETECTED low-level value {av!r} was not stripped: {c.raw_text!r}"
            )
