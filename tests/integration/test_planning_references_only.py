"""Spec 020 T007 — planning references-only + strip/smooth (real-call, US1).

Real-call (LLMXIVE_REAL_TESTS=1 + Dartmouth key, free models only). Verifies the
end-to-end planning behavior against a live backend:

- ``test_lowlevel_stripped``: a planning-stage doc asserting a WRONG low-level
  count is processed with stage_label="plan" → the specific value is removed
  (replaced by a higher-level statement), NO [UNRESOLVED-CLAIM:] marker, the gate
  is not blocked, and the citation survives (FR-002a/003/SC-001).
- ``test_fabricated_doi_blocks``: a fabricated DOI in a planning doc is flagged
  unresolvable by the reference validator (fail-closed, FR-004/SC-002) —
  independent of the low-level-claim handling.
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

# 49 is the prime-knot count at 9 crossings, NOT 13 — a wrong low-level claim that
# must be stripped (not verified, not kicked back) in a planning stage.
PLAN_DOC = (
    "# Implementation Plan\n\n"
    "## Research Question\n\n"
    "How does diagram complexity scale with the braid index?\n\n"
    "## Method\n\n"
    "We enumerate prime knots and regress crossing number on braid index. "
    "There are exactly 49 prime knots at 13 crossings, per the standard "
    "enumeration (Hoste, Thistlethwaite & Weeks 1998).\n"
)


def _backend():
    from llmxive.backends.router import make_backend

    return make_backend("dartmouth")


def test_lowlevel_stripped(tmp_path: Path) -> None:
    from llmxive.claims.service import process_document

    out, _claims, report = process_document(
        PLAN_DOC,
        artifact_path="projects/PROJ-test/specs/plan.md",
        project_id="PROJ-test",
        backend=_backend(),
        model=_FREE_MODEL,
        repo_root=tmp_path,
        stage_label="plan",
    )
    assert "49" not in out, f"specific low-level value survived planning:\n{out}"
    assert CLAIM_MARKER_PREFIX not in out, "planning emitted an unresolved-claim marker"
    assert report.blocked is False, "planning blocked on a low-level claim"
    # research question + method framing + citation preserved
    assert "braid index" in out
    assert "Hoste" in out


def test_fabricated_doi_blocks(tmp_path: Path) -> None:
    from llmxive.agents.reference_validator import (
        has_blocking_citations,
        validate_artifact,
    )

    project_id = "PROJ-999-fixture"
    relpath = f"projects/{project_id}/specs/plan.md"
    doc = (
        "# Plan\n\nWe build on prior work (doi:10.9999/totally-fake-doi-20260604).\n"
    )
    artifact = tmp_path / "projects" / project_id / "specs" / "plan.md"
    artifact.parent.mkdir(parents=True, exist_ok=True)
    artifact.write_text(doc, encoding="utf-8")
    import hashlib

    validate_artifact(
        project_id=project_id,
        artifact_path=relpath,
        artifact_text=doc,
        artifact_hash=hashlib.sha256(doc.encode("utf-8")).hexdigest(),
        repo_root=tmp_path,
    )
    assert has_blocking_citations(project_id, repo_root=tmp_path), (
        "a fabricated DOI must still block advancement in a planning stage (FR-004)"
    )
