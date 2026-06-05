"""Spec 020 T017 — a verified fact stays frozen through the real pipeline (real-call, US2).

US2's deliverable is the FREEZE: once a fact is VERIFIED, a later round must NOT re-open
or overwrite it (FR-010/011), and a later mention of the same subject adopts the frozen
value (FR-009). The freeze logic is pinned deterministically offline
(tests/unit/test_frozen_claim_cache.py); this drives it through the REAL
``process_document`` pipeline (real backend extraction + resolution path) and asserts the
frozen value survives a round that re-mentions the subject with a DIFFERENT (wrong) value
— robust to the LLM extractor's non-determinism, because the seeded VERIFIED record must
hold regardless of whether the wrong mention is extracted.

The proven-good *initial* verification of real facts (the exact OEIS count, constants,
entity facts, SC-005) is covered by the existing specs 016-019 real-call suite
(tests/real_call/test_{claim_resolve,fill_e2e,compute}_real.py).
"""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from llmxive.claims.models import Claim, ClaimKind, ClaimStatus, compute_claim_id
from llmxive.state import claims as store

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


def _backend():
    from llmxive.backends.router import make_backend

    return make_backend("dartmouth")


def _seed_verified_9988(project_id: str, repo_root: Path) -> Claim:
    raw = "There are 9,988 prime knots with 13 crossings."
    c = Claim(
        claim_id=compute_claim_id(ClaimKind.NUMERIC, raw, ""),
        kind=ClaimKind.NUMERIC, raw_text=raw, canonical=raw, context="",
        artifact_path=f"projects/{project_id}/paper/paper.md", source_type="external",
        status=ClaimStatus.VERIFIED, resolved_value="9988",
        evidence={"source_id": "OEIS:A002863", "url": "https://oeis.org/A002863"},
        resolver="oeis", attempts=1, updated_at="2026-06-04T00:00:00Z",
        source_hash=None,
    )
    store.upsert(project_id, c, repo_root=repo_root)
    return c


def test_frozen_value_survives_a_wrong_remention(tmp_path: Path) -> None:
    from llmxive.claims.service import process_document

    project_id = "PROJ-999-fixture"
    _seed_verified_9988(project_id, tmp_path)

    # A later round re-mentions the SAME subject with a WRONG value.
    doc = (
        "# Results\n\nWe find there are 27,635 prime knots with 13 crossings "
        "in the enumeration.\n"
    )
    process_document(
        doc, artifact_path=f"projects/{project_id}/paper/paper.md",
        project_id=project_id, backend=_backend(), model=_FREE_MODEL,
        repo_root=tmp_path, stage_label=None,
    )

    # FR-010/011: the VERIFIED record is immutable — still 9988, never re-opened or
    # overwritten by the wrong 27,635 mention (the freeze held through the real pipeline).
    frozen = store.load_verified_by_subject(project_id, repo_root=tmp_path)
    knot = [c for (k, sk), c in frozen.items() if "knot" in sk and "13" in sk]
    assert knot, "the seeded frozen record disappeared"
    assert all(c.resolved_value == "9988" for c in knot), (
        "a VERIFIED fact was re-opened/overwritten by a later wrong mention (FR-011)"
    )
