"""Integration test (T128): the next scheduled run resumes from the failed stage.

Pure file-fixture-driven; no LLM calls. Plants a project at `planned`
with a run-log entry whose outcome=failed; verifies the resume
helper reports the right state.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from llmxive.pipeline import resume as resume_mod
from llmxive.state import project as project_store
from llmxive.state import runlog
from llmxive.types import (
    BackendName,
    Outcome,
    Project,
    RunLogEntry,
    Stage,
)


def _bootstrap_state(repo: Path) -> None:
    for sub in ("projects", "run-log", "locks", "citations"):
        (repo / "state" / sub).mkdir(parents=True, exist_ok=True)


def test_resume_helper_detects_prior_failure(tmp_path: Path) -> None:
    repo = tmp_path
    _bootstrap_state(repo)
    now = datetime.now(timezone.utc)

    project = Project(
        id="PROJ-001-resume",
        title="Resume Test",
        field="test",
        current_stage=Stage.PLANNED,
        points_research={},
        points_paper={},
        created_at=now,
        updated_at=now,
        artifact_hashes={},
        speckit_research_dir="projects/PROJ-001-resume/specs/001-resume",
    )
    project_store.save(project, repo_root=repo)

    # Plant a failed run-log entry.
    failed = RunLogEntry(
        run_id="11111111-1111-1111-1111-111111111111",
        entry_id="22222222-2222-2222-2222-222222222222",
        agent_name="tasker",
        project_id=project.id,
        task_id="33333333-3333-3333-3333-333333333333",
        inputs=[],
        outputs=[],
        backend=BackendName.DARTMOUTH,
        model_name="qwen.qwen3.5-122b",
        prompt_version="1.0.0",
        started_at=now - timedelta(minutes=10),
        ended_at=now - timedelta(minutes=5),
        outcome=Outcome.FAILED,
        failure_reason="synthetic backend timeout",
        cost_estimate_usd=0.0,
    )
    runlog.append_entry(failed, repo_root=repo)

    assert resume_mod.needs_resume(project, repo_root=repo) is True
    assert resume_mod.last_failed_agent(project, repo_root=repo) == "tasker"


def test_resume_helper_returns_false_after_success(tmp_path: Path) -> None:
    """A success entry after the failure clears the resume flag."""
    repo = tmp_path
    _bootstrap_state(repo)
    now = datetime.now(timezone.utc)

    project = Project(
        id="PROJ-002-resumeclear",
        title="Resume Clear Test",
        field="test",
        current_stage=Stage.PLANNED,
        points_research={},
        points_paper={},
        created_at=now,
        updated_at=now,
        artifact_hashes={},
        speckit_research_dir="projects/PROJ-002-resumeclear/specs/001",
    )
    project_store.save(project, repo_root=repo)

    failed = RunLogEntry(
        run_id="aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa",
        entry_id="bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb",
        agent_name="tasker",
        project_id=project.id,
        task_id="cccccccc-cccc-cccc-cccc-cccccccccccc",
        inputs=[], outputs=[],
        backend=BackendName.DARTMOUTH,
        model_name="qwen.qwen3.5-122b",
        prompt_version="1.0.0",
        started_at=now - timedelta(minutes=20),
        ended_at=now - timedelta(minutes=15),
        outcome=Outcome.FAILED,
        cost_estimate_usd=0.0,
    )
    runlog.append_entry(failed, repo_root=repo)

    success = RunLogEntry(
        run_id="dddddddd-dddd-dddd-dddd-dddddddddddd",
        entry_id="eeeeeeee-eeee-eeee-eeee-eeeeeeeeeeee",
        agent_name="tasker",
        project_id=project.id,
        task_id="ffffffff-ffff-ffff-ffff-ffffffffffff",
        inputs=[], outputs=[],
        backend=BackendName.DARTMOUTH,
        model_name="qwen.qwen3.5-122b",
        prompt_version="1.0.0",
        started_at=now - timedelta(minutes=10),
        ended_at=now - timedelta(minutes=5),
        outcome=Outcome.SUCCESS,
        cost_estimate_usd=0.0,
    )
    runlog.append_entry(success, repo_root=repo)

    assert resume_mod.needs_resume(project, repo_root=repo) is False
    assert resume_mod.last_failed_agent(project, repo_root=repo) is None
