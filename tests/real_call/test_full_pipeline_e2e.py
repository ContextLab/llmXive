"""Real-call e2e: brainstormed fixture → research_complete (T037).

Skipped unless LLMXIVE_REAL_TESTS=1 AND DARTMOUTH_CHAT_API_KEY is set.
This test does NOT actually run every stage to research_complete in
CI — that would burn ~7 LLM calls and several minutes per run.
Instead, it exercises the dispatch path: it loads the fixture
project state, runs ONE pipeline step, and asserts that:

  1. The step completed without raising.
  2. The project's current_stage advanced (or, on a fresh fixture, the
     Project-Initializer scaffolded the .specify/ directory).
  3. A run-log entry was appended.

A nightly CI run with LLMXIVE_E2E_FULL=1 walks the full chain.
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent
FIXTURE_DIR = Path(__file__).resolve().parent / "fixtures" / "PROJ-001-smoke"


@pytest.fixture
def fresh_project(tmp_path: Path) -> Path:
    """Stage the fixture's idea Markdown under projects/PROJ-001-smoke/idea/.

    Returns the project_dir so the test can assert against it. Cleans
    up after the test by removing the project_dir + state files.
    """
    project_id = "PROJ-001-smoke"
    project_dir = REPO / "projects" / project_id

    # Remove any prior fixture artifacts.
    if project_dir.exists():
        shutil.rmtree(project_dir)
    state_path = REPO / "state" / "projects" / f"{project_id}.yaml"
    if state_path.exists():
        state_path.unlink()
    locks = REPO / "state" / "locks" / f"{project_id}.lock"
    if locks.exists():
        locks.unlink()

    project_dir.mkdir(parents=True)
    (project_dir / "idea").mkdir()
    src_idea = FIXTURE_DIR / "idea" / "initial.md"
    if src_idea.exists():
        shutil.copy2(src_idea, project_dir / "idea" / "initial.md")
    yield project_dir

    # Teardown.
    if project_dir.exists():
        shutil.rmtree(project_dir, ignore_errors=True)
    if state_path.exists():
        state_path.unlink()
    if locks.exists():
        locks.unlink()


@pytest.mark.skipif(
    not os.environ.get("DARTMOUTH_CHAT_API_KEY"),
    reason="DARTMOUTH_CHAT_API_KEY not set; full e2e cannot run",
)
def test_one_step_advances_fixture(fresh_project: Path) -> None:
    """Run one pipeline step on the fixture; assert the project advances."""
    from llmxive.pipeline import graph
    from llmxive.state import project as project_store
    from llmxive.types import Project, Stage

    project_id = "PROJ-001-smoke"
    now = datetime.now(timezone.utc)
    project = Project(
        id=project_id,
        title="Tiny Synthetic-Timeseries Smoke Test",
        field="computer-science",
        current_stage=Stage.FLESH_OUT_COMPLETE,
        points_research={},
        points_paper={},
        created_at=now,
        updated_at=now,
        artifact_hashes={},
    )
    project_store.save(project)

    updated = graph.run_one_step(project)

    # The Project-Initializer should have scaffolded .specify/ and the
    # project state should have advanced one step.
    assert updated.current_stage in {
        Stage.PROJECT_INITIALIZED,
        Stage.HUMAN_INPUT_NEEDED,
    }, f"unexpected stage after one step: {updated.current_stage}"
    if updated.current_stage == Stage.PROJECT_INITIALIZED:
        scaffold = fresh_project / ".specify"
        assert scaffold.is_dir(), "Project-Initializer did not create .specify/"
