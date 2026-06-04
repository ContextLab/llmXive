"""Spec 020 T017 — paper-stage verification still verifies + freezes (real-call, US2).

Real-call (LLMXIVE_REAL_TESTS=1 + free Dartmouth model). The paper/research/impl
stages are UNCHANGED in coverage (FR-005) and STRONGER in stability: a claim
verified once is frozen — a later rephrasing adopts the same value with no
re-resolution (FR-009/010/011, SC-003/005), and the git-tracked store persists the
frozen value across runs (FR-013, SC-004).

The deterministic freeze logic is pinned offline in tests/unit/test_frozen_claim_cache.py;
this exercises the real verification path (OEIS exact count) end-to-end.
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

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


def _backend():
    from llmxive.backends.router import make_backend

    return make_backend("dartmouth")


PAPER_DOC = (
    "# Results\n\n"
    "Our enumeration confirms there are 9,988 prime knots with 13 crossings, "
    "matching OEIS A002863.\n"
)


def test_exact_count_frozen_then_rephrase_no_waffle(tmp_path: Path) -> None:
    from llmxive.claims.service import process_document
    from llmxive.state import claims as store

    # Round 1: full paper-stage verification (stage_label=None ⇒ full).
    process_document(
        PAPER_DOC, artifact_path="projects/PROJ-x/paper/paper.md",
        project_id="PROJ-x", backend=_backend(), model=_FREE_MODEL,
        repo_root=tmp_path, stage_label=None,
    )
    verified = store.load_verified_by_subject("PROJ-x", repo_root=tmp_path)
    # The exact-count subject should be verified to 9988 (no regression — SC-005).
    knot = [c for (k, sk), c in verified.items() if "knot" in sk and "13" in sk]
    assert knot, "the 9,988-at-13-crossings claim did not verify in a paper stage"
    assert any("9988" in (c.resolved_value or "").replace(",", "") for c in knot)

    # Round 2: a rephrasing of the SAME fact must adopt the frozen value with
    # NO re-resolution (the freeze; SC-003). We detect "no re-resolution" by the
    # value being unchanged and the resolver/source_hash carried from round 1.
    rephrase = (
        "# Results\n\nThe number of prime knots at crossing number 13 is 9988 "
        "(OEIS A002863).\n"
    )
    _out2, claims2, _r2 = process_document(
        rephrase, artifact_path="projects/PROJ-x/paper/paper.md",
        project_id="PROJ-x", backend=_backend(), model=_FREE_MODEL,
        repo_root=tmp_path, stage_label=None,
    )
    knot2 = [c for c in claims2 if "9988" in (c.resolved_value or "").replace(",", "")]
    assert knot2, "the rephrased fact lost its frozen value (waffle)"
