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


def test_all_tasks_done_triggers_execute_and_gate_not_implementer(tmp_path, monkeypatch) -> None:
    """The batch→gate handoff: once every task is checked off, the NEXT
    run_one_step must run the dedicated execution gate (real analysis), NOT
    dispatch the implementer again on a fully-checked tasks.md. This is what
    turns a drained in_progress into research_complete — protect it."""
    import llmxive.execution.stage as exec_stage

    project = _in_progress_project()
    d = tmp_path / "projects" / project.id / "specs" / "001-x"
    d.mkdir(parents=True, exist_ok=True)
    (d / "tasks.md").write_text(
        "# Tasks\n\n- [X] T001 done\n- [X] T002 done\n", encoding="utf-8"
    )

    gate_called = {"n": 0}

    def _fake_gate(project_dir, *, repo_root):
        gate_called["n"] += 1  # do not actually run the sandbox

    monkeypatch.setattr(exec_stage, "execute_and_gate", _fake_gate)
    # If the implementer were (wrongly) dispatched, this would raise.
    class _BoomAgent:
        def run(self, sk_ctx):
            raise AssertionError("implementer dispatched on an all-done tasks.md")
    _wire(monkeypatch, _BoomAgent, project)

    graph.run_one_step(project, repo_root=tmp_path)

    assert gate_called["n"] == 1


def _write_pointer(tmp_path: Path, pid: str, rel_feature_dir: str) -> None:
    """Write the SSoT ``state/projects/<id>.yaml`` pointer feature_dir_for reads."""
    import yaml

    sp = tmp_path / "state" / "projects" / f"{pid}.yaml"
    sp.parent.mkdir(parents=True, exist_ok=True)
    sp.write_text(yaml.safe_dump({"speckit_research_dir": rel_feature_dir}), encoding="utf-8")


def test_task_gates_use_active_feature_dir_not_stale_lower_numbered(tmp_path) -> None:
    """A stale lower-numbered specs/* dir must NOT shadow the real (pointer-named)
    one. Reproduces PROJ-552: ``specs/001-old`` (unchecked) sorted before the real
    ``specs/010-new`` (all checked) made _all_tasks_done False forever AND pointed
    the implement-batch loop at the wrong tasks.md. The gates must resolve through
    the SSoT feature_dir_for, so they read the pointer-named active dir."""
    pid = "PROJ-771-stale-dir"
    pdir = tmp_path / "projects" / pid

    stale = pdir / "specs" / "001-old"
    stale.mkdir(parents=True)
    (stale / "tasks.md").write_text(
        "# Tasks\n\n- [ ] T001 ghost task\n- [ ] T002 ghost task\n", encoding="utf-8"
    )
    real = pdir / "specs" / "010-new"
    real.mkdir(parents=True)
    (real / "tasks.md").write_text(
        "# Tasks\n\n- [X] T001 real done\n- [X] T002 real done\n", encoding="utf-8"
    )
    _write_pointer(tmp_path, pid, f"projects/{pid}/specs/010-new")

    # Reads the active (010-new, all checked), NOT the stale lexicographically-first.
    assert graph._all_tasks_done(pdir) is True
    assert graph._incomplete_task_count(pdir, paper=False) == 0
