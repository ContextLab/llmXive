"""Spec 020 T029 / US3 — planning templates/prompts defer empirical specifics (FR-006).

US3's deliverable is the *template/prompt guidance* that steers producers to state the
research question, method, and references and to defer specific empirical values to the
implementation/research phase. That guidance is what this test pins — deterministically,
so it is a reliable regression guard (an extraction-based assertion would depend on the
LLM extractor's non-determinism on short docs, which is not what US3 changes).

The end-to-end behavior — a low-level value that still slips into a planning doc is
stripped, references still gate — is covered by the real-call US1 tests
(test_planning_references_only, test_proj552_planning_no_kickback).
"""

from __future__ import annotations

from pathlib import Path

import pytest

from llmxive.config import repo_root as _repo_root

REPO = _repo_root()

# (path, any-of these phrases must appear) — the FR-006 deferral guidance.
_DEFER_TERMS = ("defer", "research question", "reference")


def _contains_deferral(path: Path) -> bool:
    if not path.exists():
        return False
    low = path.read_text(encoding="utf-8").lower()
    # All FR-006 edits introduce the concept of "empirical" specifics; the guidance
    # is phrased either as a producer instruction ("defer ...") or a reviewer lens
    # ("cite the source / don't pre-assert ...").
    if "empirical" not in low:
        return False
    return (
        "defer" in low
        or "cite the source" in low
        or "pre-assert" in low
        or "research question" in low
    )


@pytest.mark.parametrize(
    "rel",
    [
        ".specify/templates/spec-template.md",
        ".specify/templates/plan-template.md",
        ".claude/skills/speckit-specify/SKILL.md",
        ".claude/skills/speckit-clarify/SKILL.md",
        ".claude/skills/speckit-plan/SKILL.md",
        ".claude/skills/speckit-tasks/SKILL.md",
        "agents/prompts/panels/panel_plan_data_resources.md",
    ],
)
def test_planning_guidance_defers_empirical_specifics(rel: str) -> None:
    assert _contains_deferral(REPO / rel), (
        f"{rel} is missing the FR-006 'defer specific empirical values; state RQ/method/"
        f"references' planning guidance"
    )


def test_proj552_template_copies_match_shared() -> None:
    # FR-006: per-project copies must carry the same guidance (kept in sync).
    proj = REPO / "projects/PROJ-552-quantifying-the-complexity-of-knot-diagr/.specify/templates"
    for name in ("spec-template.md", "plan-template.md"):
        shared = (REPO / ".specify/templates" / name).read_text(encoding="utf-8")
        copy = (proj / name).read_text(encoding="utf-8")
        assert shared == copy, f"PROJ-552 {name} drifted from the shared template (FR-006)"
