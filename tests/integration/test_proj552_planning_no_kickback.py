"""Spec 020 T030 / SC-006 — the PROJ-552 "49 vs 9,988" planning loop is gone (real-call).

The concrete failure that motivated spec 020: a planning document asserted "49 prime
knots at crossing 13" (wrong — 49 is the count at 9 crossings), contradicting the
plan's correct 9,988, and the panel looped on it toward escalation. Under spec 020 a
planning stage strips/generalizes the wrong count (not left, not blocked on), keeps
the citation, and advances without a low-level kickback.

Real-call (LLMXIVE_REAL_TESTS=1 + free Dartmouth model).
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

_FREE_MODEL = "qwen-2.5-72b-instruct"

PROJ552_PLAN = (
    "# Implementation Plan: Knot Diagram Complexity\n\n"
    "## Research Question\n\n"
    "How does the minimal crossing number relate to the braid index across prime knots?\n\n"
    "## Method\n\n"
    "We enumerate prime knots by crossing number and regress complexity measures. "
    "There are exactly 49 prime knots at crossing number 13, per the standard tables "
    "(Hoste, Thistlethwaite & Weeks 1998).\n\n"
    "## References\n\n"
    "- Hoste, Thistlethwaite & Weeks, *The First 1,701,936 Knots* (1998).\n"
)


def test_proj552_planning_strips_wrong_count_and_advances(tmp_path: Path) -> None:
    from llmxive.claims.service import process_document

    from llmxive.backends.router import make_backend

    out, claims, report = process_document(
        PROJ552_PLAN,
        artifact_path="projects/PROJ-552/specs/plan.md",
        project_id="PROJ-552",
        backend=make_backend("dartmouth"),
        model=_FREE_MODEL,
        repo_root=tmp_path,
        stage_label="plan",
    )
    # The wrong specific count is gone (stripped/generalized), not left, not blocked.
    assert "49" not in out, f"the wrong low-level count survived planning:\n{out}"
    assert CLAIM_MARKER_PREFIX not in out, "planning emitted a kickback marker on a low-level count"
    assert report.blocked is False, "planning blocked on a low-level count (the PROJ-552 stall)"
    # The research question, method framing, and citation are preserved.
    assert "braid index" in out
    assert "Hoste" in out
