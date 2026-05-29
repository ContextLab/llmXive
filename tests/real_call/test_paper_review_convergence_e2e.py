"""End-to-end convergence test for spec 015 T042 / FR-034.

Real-call workflow gates this on ``LLMXIVE_REAL_TESTS=1``. The test
exercises the FULL convergence-engine + adapter pipeline against a
fixture project (no external service mocks for the in-scope logic):

  1. Build a fixture home-grown project with action_items recorded.
  2. Verify the advancement evaluator's engine-adapter path writes a
     real auto-revisions round dir and leaves the project at
     PAPER_REVIEW with ``revision_spec_path`` set.
  3. Verify state/revisions/index.yaml is updated.
  4. Verify all 5 directory artifacts exist (spec/plan/tasks/analyze/result).

This test does NOT call Dartmouth: the adapter is deterministic, and
the re-review prompt assembly is pure-Python. The "real-call" gate is
here because Constitution III requires the integrated pipeline to be
tested against REAL filesystem state + REAL pydantic validation, not
mocks.
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from pathlib import Path

import pytest
import yaml

from llmxive.agents.advancement import evaluate
from llmxive.state import project as project_store
from llmxive.types import (
    ActionItem,
    BackendName,
    Project,
    ReviewerKind,
    ReviewRecord,
    Stage,
)

pytestmark = pytest.mark.skipif(
    os.environ.get("LLMXIVE_REAL_TESTS") != "1",
    reason="real-call test; set LLMXIVE_REAL_TESTS=1 to enable",
)


_NOW = datetime.now(UTC)


def _save_project(repo: Path, project_id: str, *, stage: Stage = Stage.PAPER_REVIEW) -> Project:
    (repo / "state" / "projects").mkdir(parents=True, exist_ok=True)
    proj = Project(
        id=project_id,
        title="Test paper for convergence e2e",
        field="computer science",
        current_stage=stage,
        created_at=_NOW - timedelta(days=1),
        updated_at=_NOW,
    )
    project_store.save(proj, repo_root=repo)
    return proj


def _make_home_grown(repo: Path, project_id: str) -> None:
    """Home-grown paper has paper/specs/<n>-<slug>/ (NOT arxiv-intake)."""
    (repo / "projects" / project_id / "paper" / "specs" / "001-paper").mkdir(parents=True)
    (repo / "projects" / project_id / "paper" / "specs" / "001-paper" / "spec.md").write_text("# spec\n")


def _write_review(
    repo: Path,
    project_id: str,
    reviewer_name: str,
    *,
    verdict: str,
    when: datetime,
    items: list[ActionItem] | None = None,
) -> None:
    review_dir = repo / "projects" / project_id / "paper" / "reviews"
    review_dir.mkdir(parents=True, exist_ok=True)
    score = 0.5 if verdict == "accept" else 0.0
    rec = ReviewRecord(
        reviewer_name=reviewer_name,
        reviewer_kind=ReviewerKind.LLM,
        artifact_path=f"projects/{project_id}/paper/metadata.json",
        artifact_hash="a" * 64,
        score=score,
        verdict=verdict,
        feedback="e2e fixture review",
        reviewed_at=when,
        prompt_version="1.1.0",
        model_name="qwen.qwen3.5-122b",
        backend=BackendName.DARTMOUTH,
        action_items=items or ([ActionItem.from_text("placeholder.", "writing")]
                                if verdict != "accept" else []),
    )
    front = rec.model_dump(mode="json")
    path = review_dir / f"{reviewer_name}__{when.date().isoformat()}__paper.md"
    path.write_text("---\n" + yaml.safe_dump(front, sort_keys=True) + "---\n\n# body\n")


class TestConvergenceE2E:
    def test_writing_revision_writes_auto_revisions_round_dir(self, tmp_path: Path) -> None:
        """Spec 015 T042: writing-class action items produce a
        KickbackRecord → adapter writes an auto-revisions round dir →
        project STAYS at PAPER_REVIEW with revision_spec_path set."""
        pid = "PROJ-100-e2e-writing"
        _save_project(tmp_path, pid, stage=Stage.PAPER_REVIEW)
        _make_home_grown(tmp_path, pid)
        # Write 12 specialist reviews: 11 accept, 1 minor_revision (one writing item).
        # All have the SAME artifact_hash (live).
        for slug in ("claim_accuracy", "code_quality_paper", "data_quality_paper",
                     "figure_critic", "logical_consistency", "overreach",
                     "safety_ethics", "scientific_evidence", "statistical_analysis",
                     "text_formatting", "writing_quality"):
            _write_review(tmp_path, pid, f"paper_reviewer_{slug}", verdict="accept", when=_NOW)
        _write_review(tmp_path, pid, "paper_reviewer_jargon_police",
                       verdict="minor_revision", when=_NOW,
                       items=[ActionItem.from_text("Define MLP at first use.", "writing")])

        project = project_store.load(pid, repo_root=tmp_path)
        new_project = evaluate(project, repo_root=tmp_path)
        assert new_project.current_stage == Stage.PAPER_REVIEW
        assert new_project.revision_spec_path is not None
        spec_dir = tmp_path / new_project.revision_spec_path
        assert spec_dir.is_dir()
        for name in ("spec.md", "plan.md", "tasks.md", "analyze-report.md", "result.yaml"):
            assert (spec_dir / name).is_file(), f"missing {name}"
        # Index updated
        idx = yaml.safe_load((tmp_path / "state" / "revisions" / "index.yaml").read_text())
        assert any(e["project_id"] == pid for e in idx.get("ready", []))

    def test_fatal_routes_to_brainstormed(self, tmp_path: Path) -> None:
        """One fatal action item among writing items → BRAINSTORMED."""
        pid = "PROJ-200-e2e-fatal"
        _save_project(tmp_path, pid, stage=Stage.PAPER_REVIEW)
        _make_home_grown(tmp_path, pid)
        (tmp_path / "projects" / pid / "idea").mkdir(parents=True)
        (tmp_path / "projects" / pid / "idea" / "idea.md").write_text("# Idea\n\nOriginal idea.\n")
        # Sole specialist review: fatal severity
        _write_review(tmp_path, pid, "paper_reviewer_scientific_evidence",
                       verdict="fundamental_flaws", when=_NOW,
                       items=[ActionItem.from_text("Central hypothesis is unsupportable.", "fatal")])
        project = project_store.load(pid, repo_root=tmp_path)
        new_project = evaluate(project, repo_root=tmp_path)
        assert new_project.current_stage == Stage.BRAINSTORMED
        # Idea record should have rejection rationale appended
        idea_text = (tmp_path / "projects" / pid / "idea" / "idea.md").read_text()
        assert "Rejection rationale" in idea_text
        assert "Central hypothesis is unsupportable" in idea_text

    def test_all_accept_lands_in_paper_accepted(self, tmp_path: Path) -> None:
        """Every specialist accepts → PAPER_ACCEPTED (the convergence success case)."""
        pid = "PROJ-300-e2e-accept"
        _save_project(tmp_path, pid, stage=Stage.PAPER_REVIEW)
        _make_home_grown(tmp_path, pid)
        # Every specialist accepts
        for slug in ("claim_accuracy", "code_quality_paper", "data_quality_paper",
                     "figure_critic", "jargon_police", "logical_consistency",
                     "overreach", "safety_ethics", "scientific_evidence",
                     "statistical_analysis", "text_formatting", "writing_quality"):
            _write_review(tmp_path, pid, f"paper_reviewer_{slug}", verdict="accept", when=_NOW)
        project = project_store.load(pid, repo_root=tmp_path)
        new_project = evaluate(project, repo_root=tmp_path)
        assert new_project.current_stage == Stage.PAPER_ACCEPTED
