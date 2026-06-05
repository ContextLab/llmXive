"""Spec 020 — the planning-recall addendum is wired into extract_claims (deterministic).

``extract_claims`` is an LLM call (non-deterministic), so SC-001 value removal on a
planning doc cannot be GUARANTEED per-run. What CAN be pinned deterministically is
that the planning-recall instruction — which raises the extractor's recall on
scope/metadata empirical values — is included in the prompt iff the stage is a
planning stage, and absent otherwise. This is that pin (a real in-test backend that
captures the prompt; no unittest.mock).
"""

from __future__ import annotations

from dataclasses import dataclass, field

import pytest

from llmxive.backends.base import ChatResponse
from llmxive.claims.extract import _PLANNING_RECALL_ADDENDUM, extract_claims


@dataclass
class _CapturingBackend:
    name: str = "dartmouth"
    seen: list[str] = field(default_factory=list)

    def chat(self, messages, *, model=None, max_tokens=None, temperature=None):  # type: ignore[no-untyped-def]
        self.seen.append("\n".join(getattr(m, "content", "") for m in messages))
        return ChatResponse(text="claims: []", model=model or "m", backend=self.name)


_DOC = "# Plan\n\n## Scale/Scope\n\n~27,635 prime knots at crossing number 13.\n"


@pytest.mark.parametrize("stage", ["spec", "clarify", "plan", "tasks"])
def test_planning_stage_includes_recall_addendum(stage: str) -> None:
    be = _CapturingBackend()
    extract_claims(_DOC, artifact_path="x/plan.md", backend=be, model=None,
                   repo_root=None, stage_label=stage)
    assert be.seen, "extractor made no backend call"
    assert _PLANNING_RECALL_ADDENDUM in be.seen[0], (
        "planning stage did not include the recall addendum in the extraction prompt"
    )


@pytest.mark.parametrize("stage", [None, "paper_plan", "paper_tasks", "implement"])
def test_non_planning_stage_omits_recall_addendum(stage: str | None) -> None:
    be = _CapturingBackend()
    extract_claims(_DOC, artifact_path="x/paper.md", backend=be, model=None,
                   repo_root=None, stage_label=stage)
    assert be.seen, "extractor made no backend call"
    assert _PLANNING_RECALL_ADDENDUM not in be.seen[0], (
        "a non-planning stage must NOT broaden recall (paper/impl verify all claims)"
    )


def test_addendum_targets_empirical_not_structural() -> None:
    # The addendum names the empirical kinds to catch and the structural kinds to skip.
    low = _PLANNING_RECALL_ADDENDUM.lower()
    assert "empirical" in low and "count" in low and "percentage" in low
    assert "structural" in low and "phase" in low and "bound" in low
