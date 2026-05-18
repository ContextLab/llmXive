"""Unit tests for revision_planner (spec 012 / T029)."""

from __future__ import annotations

from pathlib import Path

import pytest
import yaml

from llmxive.agents.revision_planner import (
    RevisionPlanningError,
    run_revision_pipeline,
)
from llmxive.types import ActionItem


def _make_home_grown_project(repo: Path, project_id: str) -> Path:
    """Build a minimal home-grown project layout (no arxiv-intake markers)."""
    pdir = repo / "projects" / project_id / "paper" / "specs" / "001-paper"
    pdir.mkdir(parents=True)
    (pdir / "spec.md").write_text("# spec\n", encoding="utf-8")
    return repo / "projects" / project_id


def _make_arxiv_intake_project(repo: Path, project_id: str) -> Path:
    """Build an arxiv-intake project layout (metadata.json + no specs/)."""
    pdir = repo / "projects" / project_id / "paper"
    pdir.mkdir(parents=True)
    (pdir / "metadata.json").write_text('{"arxiv_id": "2605.99999"}', encoding="utf-8")
    return repo / "projects" / project_id


class TestRunRevisionPipeline:
    def test_writing_revision_produces_5_artifacts(self, tmp_path: Path) -> None:
        _make_home_grown_project(tmp_path, "PROJ-100-test")
        items = [
            ActionItem.from_text("Add citation for Smith 2024.", "writing"),
            ActionItem.from_text("Fix typo in abstract.", "writing"),
        ]
        result = run_revision_pipeline(
            "PROJ-100-test", items, revision_kind="paper_writing", repo_root=tmp_path,
        )
        assert result.final_outcome == "ready_for_implementation"
        assert result.round_number == 1
        spec_dir = result.revision_spec_path
        assert (spec_dir / "spec.md").is_file()
        assert (spec_dir / "plan.md").is_file()
        assert (spec_dir / "tasks.md").is_file()
        assert (spec_dir / "analyze-report.md").is_file()
        assert (spec_dir / "result.yaml").is_file()

    def test_arxiv_intake_also_produces_revision_spec(self, tmp_path: Path) -> None:
        """Spec 012 → 013 (2026-05-18 clarification): arxiv-intake papers
        are NO LONGER short-circuited. The revision planner produces a
        spec for them just like home-grown papers; the implementer agent
        (spec 013, in flight) is responsible for editing paper/source/ and
        adding the contributing LLMs to the author list."""
        _make_arxiv_intake_project(tmp_path, "PROJ-200-arxiv")
        items = [ActionItem.from_text("Add a citation.", "writing")]
        result = run_revision_pipeline(
            "PROJ-200-arxiv", items, revision_kind="paper_writing", repo_root=tmp_path,
        )
        assert result.final_outcome == "ready_for_implementation"
        assert (result.revision_spec_path / "spec.md").is_file()

    def test_action_items_become_tasks(self, tmp_path: Path) -> None:
        _make_home_grown_project(tmp_path, "PROJ-100-test")
        items = [
            ActionItem.from_text("Add citation.", "writing"),
            ActionItem.from_text("Re-run baseline.", "science"),
            ActionItem.from_text("Fix typo.", "writing"),
        ]
        result = run_revision_pipeline(
            "PROJ-100-test", items, revision_kind="paper_writing", repo_root=tmp_path,
        )
        tasks_text = (result.revision_spec_path / "tasks.md").read_text()
        # One task per action item, sorted by severity (writing first, then science)
        for it in items:
            assert f"[{it.id}]" in tasks_text
        # 3 tasks total
        assert tasks_text.count("- [ ] T") == 3

    def test_seed_specify_includes_action_items(self, tmp_path: Path) -> None:
        _make_home_grown_project(tmp_path, "PROJ-100-test")
        items = [ActionItem.from_text("Add citation for Smith 2024.", "writing")]
        result = run_revision_pipeline(
            "PROJ-100-test", items, revision_kind="paper_writing", repo_root=tmp_path,
        )
        spec_text = (result.revision_spec_path / "spec.md").read_text()
        assert "Add citation for Smith 2024" in spec_text
        assert items[0].id in spec_text

    def test_science_kind_produces_science_revision_marker(self, tmp_path: Path) -> None:
        _make_home_grown_project(tmp_path, "PROJ-100-test")
        items = [ActionItem.from_text("Re-run baseline.", "science")]
        result = run_revision_pipeline(
            "PROJ-100-test", items, revision_kind="paper_science", repo_root=tmp_path,
        )
        assert result.revision_kind == "paper_science"
        spec_text = (result.revision_spec_path / "spec.md").read_text()
        assert "paper_science" in spec_text
        # result.yaml records kind
        result_yaml = yaml.safe_load((result.revision_spec_path / "result.yaml").read_text())
        assert result_yaml["revision_kind"] == "paper_science"

    def test_round_number_increments(self, tmp_path: Path) -> None:
        _make_home_grown_project(tmp_path, "PROJ-100-test")
        items = [ActionItem.from_text("x.", "writing")]
        r1 = run_revision_pipeline(
            "PROJ-100-test", items, revision_kind="paper_writing", repo_root=tmp_path,
        )
        r2 = run_revision_pipeline(
            "PROJ-100-test", items, revision_kind="paper_writing", repo_root=tmp_path,
        )
        assert r1.round_number == 1
        assert r2.round_number == 2
        assert r1.revision_spec_path != r2.revision_spec_path

    def test_index_yaml_updated(self, tmp_path: Path) -> None:
        _make_home_grown_project(tmp_path, "PROJ-100-test")
        items = [ActionItem.from_text("x.", "writing")]
        result = run_revision_pipeline(
            "PROJ-100-test", items, revision_kind="paper_writing", repo_root=tmp_path,
        )
        idx_path = tmp_path / "state" / "revisions" / "index.yaml"
        assert idx_path.is_file()
        idx = yaml.safe_load(idx_path.read_text())
        assert len(idx["ready"]) == 1
        assert idx["ready"][0]["project_id"] == "PROJ-100-test"
        assert "round-1" in idx["ready"][0]["revision_spec_path"]

    def test_result_yaml_records_stage_outcomes(self, tmp_path: Path) -> None:
        _make_home_grown_project(tmp_path, "PROJ-100-test")
        items = [ActionItem.from_text("x.", "writing")]
        result = run_revision_pipeline(
            "PROJ-100-test", items, revision_kind="paper_writing", repo_root=tmp_path,
        )
        rdata = yaml.safe_load((result.revision_spec_path / "result.yaml").read_text())
        names = [s["name"] for s in rdata["stage_results"]]
        assert names == ["specify", "clarify", "plan", "tasks", "analyze"]
        assert all(s["status"] == "success" for s in rdata["stage_results"])
        assert rdata["final_outcome"] == "ready_for_implementation"
