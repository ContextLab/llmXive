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

    # FR-003: a planning stage never emits an unresolved-claim marker or blocks on
    # a low-level value, and registers/resolves nothing.
    assert CLAIM_MARKER_PREFIX not in out, "planning emitted an [UNRESOLVED-CLAIM:] marker"
    assert report.blocked is False, "planning blocked on a low-level claim"
    assert claims == [], "planning registered/resolved low-level claims"

    # The real file on disk is untouched (read-only).
    assert _PLAN.read_text(encoding="utf-8") == original

    # SC-001: the specific wrong count "27,635 at crossing number 13" must not
    # survive as an asserted specific value (stripped/generalized).
    assert "27,635" not in out and "27635" not in out, (
        f"the wrong low-level count survived the planning stage:\n{out[:1500]}"
    )
