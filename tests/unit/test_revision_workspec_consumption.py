"""Regression: the revision implementer CONSUMES the persisted work-spec
(spec 023 US1 / FR-002).

Drives the REAL ``LLMXiveImplementer.run()`` over a hermetic repo
(``LLMXIVE_REPO_ROOT``): real registry entry, real round dir + tasks.md,
real project state, real run-log writes. Only the network boundary
(``implementer.chat_with_fallback``) is replaced with a raising fake so
the per-task LLM calls fail deterministically offline — consumption
semantics (derive round → process tasks → clear ``revision_spec_path`` →
return to the source review stage) are exactly the production path, since
the implementer clears the spec path whether or not individual tasks
succeeded (zero-success rounds feed the bounded failsafe counter instead).
"""

from __future__ import annotations

import shutil
from datetime import UTC, datetime
from pathlib import Path
from uuid import uuid4

import pytest
import yaml

from llmxive.agents import implementer as implementer_mod
from llmxive.agents import registry as registry_loader
from llmxive.agents.base import AgentContext
from llmxive.agents.implementer import LLMXiveImplementer
from llmxive.state import project as project_store
from llmxive.types import Project, Stage

REAL_REPO = Path(__file__).resolve().parents[2]
PROJ_ID = "PROJ-906-consume"


@pytest.fixture
def repo(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    (tmp_path / "agents").mkdir()
    shutil.copy(
        REAL_REPO / "agents" / "registry.yaml",
        tmp_path / "agents" / "registry.yaml",
    )
    shutil.copytree(REAL_REPO / "agents" / "prompts", tmp_path / "agents" / "prompts")
    for sub in ("projects", "run-log", "locks"):
        (tmp_path / "state" / sub).mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("LLMXIVE_REPO_ROOT", str(tmp_path))

    def _network_down(*args, **kwargs):
        raise ConnectionError("offline unit test: no LLM backend")

    monkeypatch.setattr(implementer_mod, "chat_with_fallback", _network_down)
    return tmp_path


def _bootstrap(repo: Path) -> Project:
    source_dir = repo / "projects" / PROJ_ID / "paper" / "source"
    source_dir.mkdir(parents=True)
    (source_dir / "main.tex").write_text(
        "\\documentclass{article}\\begin{document}body\\end{document}\n",
        encoding="utf-8",
    )
    round_dir = repo / "specs" / "auto-revisions" / PROJ_ID / "round-1"
    round_dir.mkdir(parents=True)
    (round_dir / "tasks.md").write_text(
        "- [ ] T001 [writing] Fix the abstract typo\n"
        "- [ ] T002 [writing] Tighten section 2\n",
        encoding="utf-8",
    )
    now = datetime.now(UTC)
    project = Project(
        id=PROJ_ID,
        title="consumption test",
        field="test",
        current_stage=Stage.PAPER_REVIEW,
        created_at=now,
        updated_at=now,
        artifact_hashes={},
        revision_spec_path=str(round_dir.relative_to(repo)),
    )
    project_store.save(project, repo_root=repo)
    return project


def _run_implementer(repo: Path) -> None:
    entry = registry_loader.get("llmxive_implementer", repo_root=repo)
    agent = LLMXiveImplementer(entry)
    ctx = AgentContext(
        project_id=PROJ_ID,
        run_id=str(uuid4()),
        task_id=str(uuid4()),
        inputs=[],
        metadata={},
    )
    agent.run(ctx)


def test_implementer_consumes_exactly_the_persisted_workspec(repo: Path) -> None:
    project = _bootstrap(repo)
    spec_rel = project.revision_spec_path

    _run_implementer(repo)

    saved = project_store.load(PROJ_ID, repo_root=repo)
    assert saved.revision_spec_path is None, (
        "the work-spec must be marked consumed (cleared) after the round"
    )
    assert saved.current_stage == Stage.PAPER_REVIEW, (
        "the project returns to the source review stage for re-review"
    )
    log_path = repo / spec_rel / "implementer-log.yaml"
    assert log_path.is_file(), "the round log must land IN the consumed round dir"
    log = yaml.safe_load(log_path.read_text(encoding="utf-8"))
    assert log["revision_spec_path"] == spec_rel
    assert log["round_number"] == 1
    assert log["total_tasks"] == 2


def test_noop_without_workspec(repo: Path) -> None:
    """A review-stage project with no work-spec is a SKIP, not a crash and
    not a state mutation."""
    project = _bootstrap(repo)
    project = project.model_copy(update={"revision_spec_path": None})
    project_store.save(project, repo_root=repo)

    _run_implementer(repo)

    saved = project_store.load(PROJ_ID, repo_root=repo)
    assert saved.current_stage == Stage.PAPER_REVIEW
    assert saved.revision_spec_path is None


def test_repeated_zero_rounds_feed_bounded_failsafe(repo: Path) -> None:
    """Three consecutive zero-success rounds trip the implementer failsafe
    (bounded discipline): the project is NOT left looping with a cleared
    spec — it either gets a diagnosed round-N+1 work-spec or halts at
    AGENT_BLOCKED for triage. With an unclassifiable all-tasks-skipped
    round the honest outcome is AGENT_BLOCKED."""
    _bootstrap(repo)
    for n in (1, 2, 3):
        round_dir = repo / "specs" / "auto-revisions" / PROJ_ID / f"round-{n}"
        round_dir.mkdir(parents=True, exist_ok=True)
        (round_dir / "tasks.md").write_text(
            f"- [ ] T00{n} [writing] task for round {n}\n", encoding="utf-8"
        )
        project = project_store.load(PROJ_ID, repo_root=repo)
        project = project.model_copy(
            update={
                "revision_spec_path": str(round_dir.relative_to(repo)),
                "current_stage": Stage.PAPER_REVIEW,
            }
        )
        project_store.save(project, repo_root=repo)
        _run_implementer(repo)

    saved = project_store.load(PROJ_ID, repo_root=repo)
    assert saved.current_stage in {Stage.AGENT_BLOCKED, Stage.PAPER_REVIEW}
    if saved.current_stage == Stage.AGENT_BLOCKED:
        assert saved.human_escalation_reason
        assert "zero-success" in saved.human_escalation_reason
    else:
        # Diagnosed path: the failsafe synthesized a NEW work-spec round.
        assert saved.revision_spec_path, (
            "after the failsafe cap the project must carry either a "
            "diagnosed work-spec or an AGENT_BLOCKED halt — never a bare loop"
        )
