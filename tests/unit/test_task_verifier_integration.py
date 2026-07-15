"""Independent task verifier wired into the real run_one_step implement batch.

After the implementer claims tasks done, a SEPARATE model (outside the implementer
session) judges whether the artifacts satisfy the requirements. These tests drive
the REAL ``run_one_step`` batch loop (only the implementer agent + store/registry +
the verifier's model boundary are stubbed) and pin the SEMANTIC-verdict wiring:
accept → stays ``[X]``; reject → ``[ ]`` + a note the next implementer reads;
transient failure → ``[~]``.

The tasks here are intentionally PATHLESS (no ``code/…`` artifact) so they bypass
the deterministic-first settle and reach the (stubbed/forced) semantic verifier —
the deterministic file-state path has its own suite (``test_verifier_deterministic``).
"""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from types import SimpleNamespace

from llmxive.agents import task_verifier as tv
from llmxive.pipeline import graph
from llmxive.state import project as project_store
from llmxive.types import Project, Stage


def _stub_entry(name: str):
    return SimpleNamespace(
        prompt_path=Path("prompts/x.md"), default_backend="dartmouth",
        fallback_backends=[], default_model="m", prompt_version="1.0.0", name=name,
    )


def _project() -> Project:
    now = datetime.now(UTC)
    return Project(
        id="PROJ-903-verify", title="X", field="computer science",
        current_stage=Stage.IN_PROGRESS, created_at=now, updated_at=now,
        speckit_research_dir="specs/001-x",
    )


def _write_tasks(tmp_path: Path, project: Project, n: int) -> Path:
    d = tmp_path / "projects" / project.id / "specs" / "001-x"
    d.mkdir(parents=True, exist_ok=True)
    t = d / "tasks.md"
    t.write_text(
        "# Tasks\n\n"
        + "".join(f"- [ ] T{i:03d} do thing {i}\n" for i in range(1, n + 1)),
        encoding="utf-8",
    )
    return t


class _CheckOffOneAgent:
    def run(self, sk_ctx) -> None:
        tasks = sorted((sk_ctx.project_dir).glob("specs/*/tasks.md"))[0]
        text = tasks.read_text(encoding="utf-8").replace("- [ ]", "- [X]", 1)
        tasks.write_text(text, encoding="utf-8")


def _wire(monkeypatch, project) -> None:
    monkeypatch.setitem(graph._SPECKIT_AGENTS, "implementer", _CheckOffOneAgent)
    monkeypatch.setattr(
        graph.registry_loader, "get", lambda name, repo_root=None: _stub_entry(name)
    )
    monkeypatch.setattr(project_store, "load", lambda pid, repo_root=None: project)
    monkeypatch.setattr(project_store, "save", lambda p, repo_root=None: None)


def _force_verdict(monkeypatch, complete, reason="r") -> None:
    monkeypatch.setattr(
        tv, "verify_task",
        lambda **k: tv.TaskVerdict(complete=complete, reason=reason),
    )


def test_accept_keeps_tasks_checked_off(tmp_path, monkeypatch) -> None:
    """The default offline verdict is COMPLETE (conftest stub) → tasks stay [X]
    and the project's tasks are all done (no [ ], no [~])."""
    project = _project()
    t = _write_tasks(tmp_path, project, n=3)
    _wire(monkeypatch, project)

    graph.run_one_step(project, repo_root=tmp_path)

    text = t.read_text(encoding="utf-8")
    assert "- [ ]" not in text and "- [~]" not in text
    assert text.count("- [X]") == 3


def test_reject_reverts_task_to_open_and_writes_notes(tmp_path, monkeypatch) -> None:
    project = _project()
    t = _write_tasks(tmp_path, project, n=3)
    _wire(monkeypatch, project)
    _force_verdict(monkeypatch, complete=False, reason="the produced output is empty")

    graph.run_one_step(project, repo_root=tmp_path)

    text = t.read_text(encoding="utf-8")
    # Every claimed task was rejected → reverted to [ ] for the implementer to redo.
    assert text.count("- [ ]") == 3
    assert "- [X]" not in text
    notes = tmp_path / "projects" / project.id / ".specify" / "memory" / "task_verifier_notes.md"
    assert notes.is_file()
    assert "the produced output is empty" in notes.read_text(encoding="utf-8")


def test_defer_marks_task_under_review_and_blocks_advancement(tmp_path, monkeypatch) -> None:
    """A transient verifier failure marks the task [~] (under review): it counts as
    incomplete so the project cannot advance, and is re-verified next tick."""
    project = _project()
    t = _write_tasks(tmp_path, project, n=3)
    _wire(monkeypatch, project)
    _force_verdict(monkeypatch, complete=None, reason="(verifier unreachable)")

    graph.run_one_step(project, repo_root=tmp_path)

    text = t.read_text(encoding="utf-8")
    assert text.count("- [~]") == 3 and "- [X]" not in text
    project_dir = tmp_path / "projects" / project.id
    assert not graph._all_tasks_done(project_dir)
    assert graph._incomplete_task_count(project_dir, paper=False) == 3


def test_already_verified_tasks_are_not_rejudged(tmp_path, monkeypatch) -> None:
    """A task that was ALREADY [X] before the tick is settled — the verify pass
    must not re-judge it (so a flaky reject can't un-settle accepted work)."""
    project = _project()
    d = tmp_path / "projects" / project.id / "specs" / "001-x"
    d.mkdir(parents=True, exist_ok=True)
    t = d / "tasks.md"
    # T001 pre-accepted ([X]); T002 still open and will be claimed this tick.
    t.write_text(
        "# Tasks\n\n- [X] T001 prior work\n- [ ] T002 new work\n",
        encoding="utf-8",
    )
    _wire(monkeypatch, project)
    calls: list[str] = []

    def _spy(**k):
        calls.append(k["task_text"])
        return tv.TaskVerdict(complete=True, reason="ok")

    monkeypatch.setattr(tv, "verify_task", _spy)
    graph.run_one_step(project, repo_root=tmp_path)

    # Only the newly-claimed T002 is judged; the settled T001 is skipped.
    assert any("T002" in c for c in calls)
    assert not any("T001" in c for c in calls)
