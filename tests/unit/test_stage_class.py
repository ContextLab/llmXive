"""Spec 020 T003 — stage classification (C1 contract, FR-001).

Offline truth table for ``claims/stage.py::is_planning_stage`` and the
``PLANNING_STAGE_LABELS`` single source of truth. Planning = the speckit
specify/clarify/plan/tasks artifacts (which emit stage_label "spec"/"plan"/
"tasks", plus the conceptual aliases). Paper/research/impl stages and an
unknown/None label fall through to FULL verification (fail-safe toward more
verification, never less).
"""

from __future__ import annotations

import pytest

from llmxive.claims.stage import PLANNING_STAGE_LABELS, is_planning_stage


@pytest.mark.parametrize("label", ["spec", "specify", "clarify", "plan", "tasks"])
def test_planning_labels_are_planning(label: str) -> None:
    assert is_planning_stage(label) is True


@pytest.mark.parametrize(
    "label",
    ["paper_spec", "paper_plan", "paper_tasks", "paper", "implement", "research",
     "unknown", "", None],
)
def test_non_planning_labels_are_full(label: str | None) -> None:
    assert is_planning_stage(label) is False


def test_paper_labels_do_not_substring_match_planning() -> None:
    # "paper_spec" contains "spec" — exact membership must NOT classify it planning.
    assert is_planning_stage("paper_spec") is False
    assert is_planning_stage("paper_plan") is False
    assert is_planning_stage("paper_tasks") is False


def test_planning_set_contents() -> None:
    # The actual emitters (clarify_cmd->"spec", plan_cmd->"plan", tasks_cmd->"tasks")
    # MUST be members; the conceptual aliases are allowed for forward-compat.
    assert {"spec", "plan", "tasks"} <= PLANNING_STAGE_LABELS
    assert "paper_spec" not in PLANNING_STAGE_LABELS
    assert "paper_plan" not in PLANNING_STAGE_LABELS
    assert "paper_tasks" not in PLANNING_STAGE_LABELS
    assert isinstance(PLANNING_STAGE_LABELS, frozenset)
