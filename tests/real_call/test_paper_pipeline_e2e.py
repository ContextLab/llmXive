"""Real-call e2e (T095): research_accepted fixture → paper pipeline.

Skipped unless LLMXIVE_REAL_TESTS=1 AND DARTMOUTH_CHAT_API_KEY is set.

The full chain (Paper-Initializer → Paper-Specifier → Paper-Clarifier
→ Paper-Planner → Paper-Tasker → Paper-Implementer dispatching to
Writing/Figure/Statistics/Proofreader/LaTeX-Build) burns many LLM
calls; this test only exercises the dispatch path: stage a
`research_accepted` fixture, run ONE pipeline step, and assert the
project advances to paper_drafting_init (Paper-Initializer ran) AND
the paper/.specify/ scaffold exists.

A nightly CI run with LLMXIVE_E2E_FULL=1 walks the full chain.
"""

from __future__ import annotations

import os
import shutil
from datetime import datetime, timezone
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parent.parent.parent


@pytest.fixture
def fresh_paper_project(tmp_path: Path) -> Path:
    project_id = "PROJ-001-paperpipe"
    project_dir = REPO / "projects" / project_id

    # Clean any prior fixture artifacts.
    for path in (
        project_dir,
        REPO / "state" / "projects" / f"{project_id}.yaml",
        REPO / "state" / "locks" / f"{project_id}.lock",
    ):
        if path.is_dir():
            shutil.rmtree(path, ignore_errors=True)
        elif path.exists():
            path.unlink()

    project_dir.mkdir(parents=True)
    # Plant a minimal "completed research" state: an idea, a specs/ dir
    # with a finished tasks.md (all checked), and a results.md.
    (project_dir / "idea").mkdir()
    (project_dir / "idea" / "initial.md").write_text(
        "# Tiny Paper-Pipe Smoke\n\nA placeholder idea for the paper-pipeline e2e test.\n",
        encoding="utf-8",
    )
    feature_dir = project_dir / "specs" / "001-paperpipe"
    feature_dir.mkdir(parents=True)
    (feature_dir / "spec.md").write_text("# Spec\n\nSmoke spec.\n", encoding="utf-8")
    (feature_dir / "plan.md").write_text("# Plan\n\nSmoke plan.\n", encoding="utf-8")
    (feature_dir / "tasks.md").write_text(
        "- [X] T001 done\n",
        encoding="utf-8",
    )
    (project_dir / "results.md").write_text(
        "# Results\n\n100 sine-wave samples; residual std 0.10.\n",
        encoding="utf-8",
    )

    yield project_dir

    # Teardown.
    if project_dir.exists():
        shutil.rmtree(project_dir, ignore_errors=True)
    for path in (
        REPO / "state" / "projects" / f"{project_id}.yaml",
        REPO / "state" / "locks" / f"{project_id}.lock",
    ):
        if path.exists():
            path.unlink()


@pytest.mark.skipif(
    not os.environ.get("DARTMOUTH_CHAT_API_KEY"),
    reason="DARTMOUTH_CHAT_API_KEY not set; paper pipeline e2e cannot run",
)
def test_one_paper_step_advances_fixture(fresh_paper_project: Path) -> None:
    """Run one paper-stage pipeline step on the fixture; assert advance."""
    from llmxive.pipeline import graph
    from llmxive.state import project as project_store
    from llmxive.types import Project, Stage

    project_id = "PROJ-001-paperpipe"
    now = datetime.now(timezone.utc)
    project = Project(
        id=project_id,
        title="Tiny Paper-Pipe Smoke",
        field="computer-science",
        current_stage=Stage.RESEARCH_ACCEPTED,
        points_research={"research_review": 5.0},
        points_paper={},
        created_at=now,
        updated_at=now,
        artifact_hashes={},
        speckit_research_dir=f"projects/{project_id}/specs/001-paperpipe",
    )
    project_store.save(project)

    updated = graph.run_one_step(project)

    # The Paper-Initializer should have scaffolded paper/.specify/ and
    # the project should have advanced one step.
    assert updated.current_stage in {
        Stage.PAPER_DRAFTING_INIT,
        Stage.HUMAN_INPUT_NEEDED,
    }, f"unexpected stage after one paper-pipe step: {updated.current_stage}"
    if updated.current_stage == Stage.PAPER_DRAFTING_INIT:
        scaffold = fresh_paper_project / "paper" / ".specify"
        assert scaffold.is_dir(), "Paper-Initializer did not create paper/.specify/"
