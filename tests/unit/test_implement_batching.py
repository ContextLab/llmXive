"""Implement-stage batching (the universal in_progress wall).

The speckit implementer checks off ONE task per run, but a research project
carries 50-60 tasks and the load-balanced scheduler picks any single stage only
a fraction of the time — so at one task/tick NO project ever drained
``in_progress`` (zero projects had EVER reached ``research_complete``). When an
implement-stage project is picked, ``run_one_step`` now drains up to
``IMPLEMENT_TASK_BATCH`` tasks that tick (bounded by a wall-clock budget and a
strict progress guard). These tests exercise the REAL ``run_one_step`` batch
loop; only the implementer agent + registry/store collaborators are stubbed.
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from llmxive.pipeline import graph
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


def _stub_entry(name: str):
    return SimpleNamespace(
        prompt_path=Path("prompts/x.md"),
        default_backend="dartmouth",
        fallback_backends=[],
        default_model="m",
        prompt_version="1.0.0",
        name=name,
    )


def _in_progress_project() -> Project:
    now = datetime.now(UTC)
    return Project(
        id="PROJ-902-batch",
        title="X",
        field="computer science",
        current_stage=Stage.IN_PROGRESS,
        created_at=now,
        updated_at=now,
        speckit_research_dir="specs/001-x",
    )


def _write_tasks(tmp_path: Path, project: Project, n: int) -> Path:
    d = tmp_path / "projects" / project.id / "specs" / "001-x"
    d.mkdir(parents=True, exist_ok=True)
    t = d / "tasks.md"
    t.write_text(
        "# Tasks\n\n"
        + "".join(f"- [ ] T{i:03d} do thing {i} in code/a{i}.py\n" for i in range(1, n + 1)),
        encoding="utf-8",
    )
    return t


def _wire(monkeypatch, agent_cls, project) -> None:
    monkeypatch.setitem(graph._SPECKIT_AGENTS, "implementer", agent_cls)
    monkeypatch.setattr(
        graph.registry_loader, "get", lambda name, repo_root=None: _stub_entry(name)
    )
    monkeypatch.setattr(project_store, "load", lambda pid, repo_root=None: project)
    monkeypatch.setattr(project_store, "save", lambda p, repo_root=None: None)


class _CheckOffOneAgent:
    """Fake speckit implementer: checks off the first `[ ]` per run (the real
    one-task-per-run contract), counting invocations."""

    runs = 0

    def run(self, sk_ctx) -> None:
        type(self).runs += 1
        tasks = sorted((sk_ctx.project_dir).glob("specs/*/tasks.md"))[0]
        text = tasks.read_text(encoding="utf-8")
        text = text.replace("- [ ]", "- [X]", 1)  # first incomplete -> done
        tasks.write_text(text, encoding="utf-8")


def test_batch_drains_multiple_tasks_in_one_tick(tmp_path, monkeypatch) -> None:
    project = _in_progress_project()
    t = _write_tasks(tmp_path, project, n=5)
    _CheckOffOneAgent.runs = 0
    _wire(monkeypatch, _CheckOffOneAgent, project)

    graph.run_one_step(project, repo_root=tmp_path)

    # All 5 tasks drained in a SINGLE tick (pre-fix: only 1).
    assert _CheckOffOneAgent.runs == 5
    assert "- [ ]" not in t.read_text(encoding="utf-8")


def test_batch_respects_the_cap(tmp_path, monkeypatch) -> None:
    from llmxive.config import IMPLEMENT_TASK_BATCH

    project = _in_progress_project()
    t = _write_tasks(tmp_path, project, n=IMPLEMENT_TASK_BATCH + 7)
    _CheckOffOneAgent.runs = 0
    _wire(monkeypatch, _CheckOffOneAgent, project)

    graph.run_one_step(project, repo_root=tmp_path)

    # Exactly IMPLEMENT_TASK_BATCH tasks this tick; the rest wait for next tick.
    assert _CheckOffOneAgent.runs == IMPLEMENT_TASK_BATCH
    assert t.read_text(encoding="utf-8").count("- [ ]") == 7


class _NoProgressAgent:
    """A run that fails to check off its task must NOT spin the batch."""

    runs = 0

    def run(self, sk_ctx) -> None:
        type(self).runs += 1  # leaves tasks.md untouched


def test_batch_stops_on_no_progress(tmp_path, monkeypatch) -> None:
    project = _in_progress_project()
    _write_tasks(tmp_path, project, n=5)
    _NoProgressAgent.runs = 0
    _wire(monkeypatch, _NoProgressAgent, project)

    graph.run_one_step(project, repo_root=tmp_path)

    # The progress guard stops after ONE no-op pass — never an infinite loop.
    assert _NoProgressAgent.runs == 1
