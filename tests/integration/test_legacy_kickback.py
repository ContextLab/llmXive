"""Integration tests for the legacy-revision → KickbackRecord adapter
(spec 015 T042, discrepancy #6).

Verifies that BOTH legacy paper-revision routing schemes can be expressed
as a single ``KickbackRecord`` shape — closing the design's call to
unify the two parallel revision schemes (graph.py transient stages vs
advancement.py + revision_planner.py spec-012 scheme).
"""

from __future__ import annotations

from llmxive.convergence.legacy_kickback import (
    kickback_from_graph_stage,
    kickback_from_revision_planner,
    legacy_revision_stages,
)
from llmxive.convergence.types import Severity


def test_kickback_from_research_minor_revision():
    kb = kickback_from_graph_stage("research_minor_revision", project_id="PROJ-001-x")
    assert kb is not None
    assert kb.from_stage == "research_minor_revision"
    assert kb.to_stage == "tasked"
    assert kb.worst_severity == Severity.REQUIREMENT
    assert "PROJ-001-x" in kb.reason
    assert "re-task" in kb.reason


def test_kickback_from_research_full_revision():
    kb = kickback_from_graph_stage("research_full_revision")
    assert kb is not None
    assert kb.to_stage == "clarified"
    assert kb.worst_severity == Severity.METHODOLOGY


def test_kickback_from_research_rejected():
    kb = kickback_from_graph_stage("research_rejected")
    assert kb is not None
    assert kb.to_stage == "brainstormed"
    assert kb.worst_severity == Severity.FATAL


def test_kickback_from_paper_minor_revision():
    kb = kickback_from_graph_stage("paper_minor_revision")
    assert kb is not None
    assert kb.to_stage == "paper_tasked"
    assert kb.worst_severity == Severity.WRITING


def test_kickback_from_paper_major_revision_writing():
    kb = kickback_from_graph_stage("paper_major_revision_writing")
    assert kb is not None
    assert kb.to_stage == "paper_clarified"
    assert kb.worst_severity == Severity.WRITING


def test_kickback_from_paper_major_revision_science_routes_to_research_side():
    """Science-class paper revision MUST route back to research-side
    (``clarified``), not paper-side — the new engine's adaptive kickback
    follows the same rule."""
    kb = kickback_from_graph_stage("paper_major_revision_science")
    assert kb is not None
    assert kb.to_stage == "clarified"  # research side!
    assert kb.worst_severity == Severity.SCIENCE


def test_kickback_from_paper_fundamental_flaws():
    kb = kickback_from_graph_stage("paper_fundamental_flaws")
    assert kb is not None
    assert kb.to_stage == "brainstormed"
    assert kb.worst_severity == Severity.FATAL


def test_kickback_from_graph_stage_returns_none_for_non_revision_stage():
    """Non-revision stages (e.g. ``specified``, ``tasked``) MUST NOT be
    converted — they aren't revision events."""
    assert kickback_from_graph_stage("specified") is None
    assert kickback_from_graph_stage("tasked") is None
    assert kickback_from_graph_stage("not_a_real_stage") is None


def test_kickback_from_revision_planner_ready_for_implementation():
    kb = kickback_from_revision_planner(
        "ready_for_implementation",
        revision_spec_path="specs/000-revision/spec.md",
        project_id="PROJ-001-x",
    )
    assert kb is not None
    assert kb.from_stage == "paper_revision_in_progress"
    assert kb.to_stage == "ready_for_implementation"
    assert kb.worst_severity == Severity.WRITING
    assert "specs/000-revision/spec.md" in kb.artifact_links
    assert "PROJ-001-x" in kb.reason


def test_kickback_from_revision_planner_blocked():
    kb = kickback_from_revision_planner("paper_revision_blocked")
    assert kb is not None
    assert kb.to_stage == "paper_revision_blocked"
    assert kb.worst_severity == Severity.FATAL
    assert "unblock" in kb.reason


def test_kickback_from_revision_planner_returns_none_for_unknown_outcome():
    """Unknown outcomes return None — the adapter is honest about what
    it can convert."""
    assert kickback_from_revision_planner("not_an_outcome") is None


def test_legacy_revision_stages_covers_both_schemes():
    """The set should contain every stage from BOTH legacy schemes —
    used by audit sweeps that need to know "what stages does the engine
    NOT yet own"."""
    stages = legacy_revision_stages()
    # graph.py scheme
    assert "research_minor_revision" in stages
    assert "research_full_revision" in stages
    assert "research_rejected" in stages
    assert "paper_minor_revision" in stages
    assert "paper_major_revision_writing" in stages
    assert "paper_major_revision_science" in stages
    assert "paper_fundamental_flaws" in stages
    # spec-012 scheme
    assert "paper_revision_in_progress" in stages
    assert "ready_for_implementation" in stages
    assert "paper_revision_blocked" in stages
    # exactly these 10 stages (no extras, no missing)
    assert len(stages) == 10


def test_reason_field_carries_legacy_marker():
    """Every adapted KickbackRecord MUST identify itself as legacy-sourced
    so dashboards + audits can distinguish engine-native records from
    adapted ones until the migration completes."""
    a = kickback_from_graph_stage("research_minor_revision")
    b = kickback_from_revision_planner("ready_for_implementation")
    assert a is not None and "[legacy" in a.reason
    assert b is not None and "[legacy" in b.reason
