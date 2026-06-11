"""Spec 020 — deterministic empirical-value strip + the planning GUARANTEE (offline).

``planning_scan.strip_empirical_values`` removes high-confidence empirical values
(comma-grouped counts, percentages, timed quantities) while preserving structural
numbers. The integration test proves the GUARANTEE: even when the LLM extractor
returns ZERO claims (its non-deterministic worst case), the planning branch still
strips the empirical value via this deterministic pass.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import pytest

from llmxive.claims import service as svc
from llmxive.claims.gate import CLAIM_MARKER_PREFIX
from llmxive.claims.planning_scan import has_empirical_value, strip_empirical_values


@pytest.mark.parametrize(
    "text,gone",
    [
        ("There are 27,635 prime knots.", "27,635"),
        ("~2,000 prime knots downloaded.", "2,000"),
        ("approximately 95% of records are clean.", "95%"),
        ("The first 1,701,936 knots.", "1,701,936"),
        ("Ingest takes approximately 15 minutes.", "15 minutes"),
    ],
)
def test_strips_empirical(text: str, gone: str) -> None:
    out = strip_empirical_values(text)
    assert gone not in out
    assert not has_empirical_value(out)


@pytest.mark.parametrize(
    "text,kept",
    [
        ("prime knots at ≤13 crossings", "13"),       # scope bound
        ("crossing number 13", "13"),                  # index
        ("crossing numbers 1-10", "1-10"),             # range
        ("Phase 1 analysis", "Phase 1"),               # phase
        ("checksummed via SHA-256", "SHA-256"),        # identifier
        ("version 1.0.0 ratified", "1.0.0"),           # version
        ("on 2026-05-29", "2026-05-29"),               # date
        ("citation title overlap ≥0.7", "0.7"),        # bare decimal threshold
        ("dataset ds002800", "ds002800"),              # dataset id
        # Spec 023 defect #16: bound-led values are CHOSEN DESIGN TARGETS
        # (requirements the project sets), not empirical claims — stripping
        # them made every success criterion untestable and put the
        # testability reviewers at war with the strip (observed live on
        # PROJ-552's spec panel: the reviser restored "≥80%", the strip
        # deleted it, the reviewer re-flagged the hole, forever).
        ("≥95% data completeness.", "95%"),            # target
        ("reference coverage ≥10%.", "10%"),           # target
        ("Complete within 15 minutes.", "15 minutes"),  # time budget
        ("at least 80% statistical power", "80%"),     # target
        ("minimum 80% power", "80%"),                  # target
        # Spec 023 #16b: bare timed values are design parameters
        # (timeouts/backoffs/budgets), never world-claims.
        ("Exponential backoff (1s → 60s max).", "60s"),
        ("per-pass timeout 30 ms", "30 ms"),
    ],
)
def test_preserves_structural(text: str, kept: str) -> None:
    assert kept in strip_empirical_values(text)


def test_idempotent_and_headers_and_fences() -> None:
    doc = (
        "# Heading with 27,635 in it\n"
        "There are 27,635 knots, ≥95% complete.\n"
        "```\ncode with 1,234 stays\n```\n"
    )
    once = strip_empirical_values(doc)
    # header line + fenced code are untouched
    assert "# Heading with 27,635 in it" in once
    assert "code with 1,234 stays" in once
    # the prose claim value is deferred; the bound-led target survives (#16)
    assert "27,635 knots" not in once.split("\n")[1]
    assert "≥95% complete" in once
    assert strip_empirical_values(once) == once  # idempotent


def _lowlevel_claim_doc() -> str:
    return (
        "# Plan\n\n## Scale/Scope\n\n"
        "~2,000 prime knots (1-10), ~27,635 at crossing number 13 (Phase 1).\n"
    )


def test_planning_branch_guarantees_strip_even_when_extractor_finds_nothing(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    # Simulate the LLM extractor's worst case: it returns ZERO claims. The
    # deterministic pass must STILL strip the empirical values (the guarantee).
    monkeypatch.setattr(svc, "extract_claims", lambda *a, **k: [])

    def _boom(*a: Any, **k: Any) -> Any:
        raise AssertionError("resolve() called in a planning stage")

    monkeypatch.setattr(svc, "resolve", _boom)

    out, claims, report = svc.process_document(
        _lowlevel_claim_doc(),
        artifact_path="projects/PROJ-x/specs/plan.md",
        project_id="PROJ-x", backend=object(), model=None,
        repo_root=tmp_path, stage_label="plan",
    )
    assert "27,635" not in out and "2,000" not in out      # stripped (guaranteed)
    assert "crossing number 13" in out and "Phase 1" in out  # structural preserved
    assert CLAIM_MARKER_PREFIX not in out                   # still no kickback
    assert report.blocked is False
    assert claims == []
