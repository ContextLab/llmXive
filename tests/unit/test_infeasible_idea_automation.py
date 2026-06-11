"""Regression: infeasible-idea de-escalation automation (spec 023 / FR-014).

Pre-023, a flesh-out "out of feasible scope" verdict parked the project at
``human_input_needed`` with an instruction the system itself printed and
could have executed (three live projects sat exactly there — issue #303).
Now: archive the idea, write a constrained re-brainstorm instruction to
the existing ``idea/kickback_feedback.md`` injection point, route back to
BRAINSTORMED — bounded by IDEA_RETRY_CAP, then the honest terminal
``VALIDATOR_REJECTED``. No path writes ``human_input_needed``.
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path

import pytest

from llmxive.pipeline import graph, scheduler
from llmxive.pipeline._kickback import IDEA_RETRY_CAP
from llmxive.state import project as project_store
from llmxive.types import Project, Stage

REAL_REPO = Path(__file__).resolve().parents[2]
PROJ_ID = "PROJ-908-infeasible"


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "agents").mkdir()
    shutil.copy(
        REAL_REPO / "agents" / "registry.yaml",
        tmp_path / "agents" / "registry.yaml",
    )
    for sub in ("projects", "run-log", "locks"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)

    monkeypatch.setattr(graph, "run_agent", lambda agent, ctx, *, repo_root=None: None)
    return tmp_path


def _bootstrap(repo: Path) -> Project:
    idea_dir = repo / "projects" / PROJ_ID / "idea"
    idea_dir.mkdir(parents=True, exist_ok=True)
    (idea_dir / "wet-lab-idea.md").write_text(
        "# Grand wet-lab study\nRequires a particle accelerator.\n",
        encoding="utf-8",
    )
    now = datetime.now(UTC)
    project = Project(
        id=PROJ_ID,
        title="infeasible idea",
        field="test",
        current_stage=Stage.BRAINSTORMED,
        created_at=now,
        updated_at=now,
        artifact_hashes={},
    )
    project_store.save(project, repo_root=repo)
    return project


def _mark_scope_rejected(repo: Path, reason: str = "needs a particle accelerator") -> None:
    marker = repo / "projects" / PROJ_ID / ".specify" / "memory" / "scope_rejected.yaml"
    marker.parent.mkdir(parents=True, exist_ok=True)
    marker.write_text(f"reason: {reason}\n", encoding="utf-8")


def test_scope_rejection_archives_and_rebrainstorms(repo: Path) -> None:
    project = _bootstrap(repo)
    _mark_scope_rejected(repo)

    out = graph.run_one_step(project, repo_root=repo)

    assert out.current_stage == Stage.BRAINSTORMED, "constrained re-brainstorm, not a human park"
    idea_dir = repo / "projects" / PROJ_ID / "idea"
    assert not (idea_dir / "wet-lab-idea.md").exists(), "rejected idea archived"
    assert list((idea_dir / ".archive").glob("*wet-lab-idea.md")), "archive holds the body"
    feedback = (idea_dir / "kickback_feedback.md").read_text(encoding="utf-8")
    assert "particle accelerator" in feedback, "the infeasibility reason is in the constraint"
    assert "SUBSTANTIALLY DIFFERENT" in feedback
    assert "Grand wet-lab study" in feedback, "the archived body is shown for reference"
    # The marker was consumed; no human escalation anywhere.
    assert not (
        repo / "projects" / PROJ_ID / ".specify" / "memory" / "scope_rejected.yaml"
    ).exists()
    assert out.current_stage != Stage.HUMAN_INPUT_NEEDED
    assert not (
        repo / "projects" / PROJ_ID / ".specify" / "memory" / "human_input_needed.yaml"
    ).exists()


def test_cap_exhaustion_takes_honest_terminal(repo: Path) -> None:
    project = _bootstrap(repo)
    for attempt in range(1, IDEA_RETRY_CAP + 2):
        # Each cycle: flesh-out rejects again.
        (repo / "projects" / PROJ_ID / "idea").mkdir(parents=True, exist_ok=True)
        (repo / "projects" / PROJ_ID / "idea" / f"retry-{attempt}.md").write_text(
            f"# Retry {attempt}\nstill infeasible\n", encoding="utf-8"
        )
        _mark_scope_rejected(repo)
        project = graph.run_one_step(project, repo_root=repo)
        if attempt <= IDEA_RETRY_CAP:
            assert project.current_stage == Stage.BRAINSTORMED, (
                f"attempt {attempt} of {IDEA_RETRY_CAP} keeps retrying"
            )
        else:
            assert project.current_stage == Stage.VALIDATOR_REJECTED, (
                "cap exhausted → honest terminal, never human_input_needed"
            )
    saved = project_store.load(PROJ_ID, repo_root=repo)
    assert saved.current_stage == Stage.VALIDATOR_REJECTED


def test_terminal_is_never_scheduled(repo: Path) -> None:
    project = _bootstrap(repo)
    project_store.save(
        project.model_copy(update={"current_stage": Stage.VALIDATOR_REJECTED}),
        repo_root=repo,
    )
    import random

    for seed in range(50):
        assert scheduler.pick_next(repo_root=repo, rng=random.Random(seed)) is None


def test_validator_rejection_is_bounded_too(repo: Path) -> None:
    """The validator's reject→re-brainstorm cycle uses the same cap — an
    unbounded reject loop is the same defect class (FR-014)."""
    project = _bootstrap(repo)
    project = project.model_copy(update={"current_stage": Stage.FLESH_OUT_COMPLETE})
    project_store.save(project, repo_root=repo)
    mem = repo / "projects" / PROJ_ID / ".specify" / "memory"
    mem.mkdir(parents=True, exist_ok=True)
    for attempt in range(1, IDEA_RETRY_CAP + 2):
        (mem / "research_question_rejected.yaml").write_text(
            "reason: weak idea\n", encoding="utf-8"
        )
        project = graph.run_one_step(project, repo_root=repo)
        if attempt <= IDEA_RETRY_CAP:
            assert project.current_stage == Stage.BRAINSTORMED
            # Simulate the next flesh-out completing so the validator can
            # run (and reject) again.
            project = project.model_copy(
                update={"current_stage": Stage.FLESH_OUT_COMPLETE}
            )
            project_store.save(project, repo_root=repo)
        else:
            assert project.current_stage == Stage.VALIDATOR_REJECTED
