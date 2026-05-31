"""Unit tests for `llmxive project unblock-agent` (spec 015 / FR-034)."""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from pathlib import Path

from llmxive.cli import build_parser
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


def _build_project(
    repo: Path, project_id: str, stage: Stage = Stage.AGENT_BLOCKED,
    *, updated_at: datetime | None = None,
) -> Project:
    """Write a project state YAML at the given stage."""
    (repo / "state" / "projects").mkdir(parents=True, exist_ok=True)
    now = updated_at or datetime.now(UTC)
    project = Project(
        id=project_id,
        title="Test paper",
        field="computer science",
        current_stage=stage,
        created_at=now - timedelta(days=1),
        updated_at=now,
    )
    project_store.save(project, repo_root=repo)
    return project


def _make_auto_revisions_file(
    repo: Path, project_id: str, *, mtime_offset_s: int = 60,
) -> Path:
    """Create specs/auto-revisions/<id>/round-1/tasks.md with mtime offset."""
    d = repo / "specs" / "auto-revisions" / project_id / "round-1"
    d.mkdir(parents=True, exist_ok=True)
    p = d / "tasks.md"
    p.write_text("- [ ] T001 [REV] do the work\n", encoding="utf-8")
    import os
    target = datetime.now(UTC).timestamp() + mtime_offset_s
    os.utime(p, (target, target))
    return p


def _run_cli(args: list[str], cwd: Path) -> int:
    """Invoke build_parser/main, redirecting cwd to a fixture."""
    import os
    parser = build_parser()
    parsed = parser.parse_args(args)
    old_cwd = os.getcwd()
    try:
        os.chdir(cwd)
        return int(parsed.func(parsed))
    finally:
        os.chdir(old_cwd)


class TestProjectUnblockAgent:
    def test_unblock_with_edited_round_file_succeeds(self, tmp_path: Path) -> None:
        pid = "PROJ-100-test"
        _build_project(tmp_path, pid)
        _make_auto_revisions_file(tmp_path, pid, mtime_offset_s=300)
        rc = _run_cli(["project", "unblock-agent", pid], cwd=tmp_path)
        assert rc == 0
        project = project_store.load(pid, repo_root=tmp_path)
        assert project.current_stage == Stage.PAPER_REVIEW

    def test_unblock_to_research_review(self, tmp_path: Path) -> None:
        pid = "PROJ-100-test"
        _build_project(tmp_path, pid)
        _make_auto_revisions_file(tmp_path, pid, mtime_offset_s=300)
        rc = _run_cli(["project", "unblock-agent", pid, "--to-research"], cwd=tmp_path)
        assert rc == 0
        project = project_store.load(pid, repo_root=tmp_path)
        assert project.current_stage == Stage.RESEARCH_REVIEW

    def test_unblock_refuses_when_file_not_edited(self, tmp_path: Path) -> None:
        pid = "PROJ-100-test"
        # project.updated_at is in the FUTURE relative to the round file
        _build_project(tmp_path, pid, updated_at=datetime.now(UTC) + timedelta(hours=1))
        _make_auto_revisions_file(tmp_path, pid, mtime_offset_s=-3600)
        rc = _run_cli(["project", "unblock-agent", pid], cwd=tmp_path)
        assert rc != 0
        # Stage MUST be unchanged
        project = project_store.load(pid, repo_root=tmp_path)
        assert project.current_stage == Stage.AGENT_BLOCKED

    def test_unblock_refuses_on_wrong_stage(self, tmp_path: Path) -> None:
        pid = "PROJ-100-test"
        _build_project(tmp_path, pid, stage=Stage.PAPER_REVIEW)
        _make_auto_revisions_file(tmp_path, pid, mtime_offset_s=300)
        rc = _run_cli(["project", "unblock-agent", pid], cwd=tmp_path)
        assert rc != 0
        project = project_store.load(pid, repo_root=tmp_path)
        assert project.current_stage == Stage.PAPER_REVIEW

    def test_unblock_refuses_when_no_round_files(self, tmp_path: Path) -> None:
        pid = "PROJ-100-test"
        _build_project(tmp_path, pid)
        # No round files at all
        rc = _run_cli(["project", "unblock-agent", pid], cwd=tmp_path)
        assert rc != 0
