"""An accepted task whose files changed is judged again once, on the final state.

Reliability batch 1 (2026-10-11): 269 verifier calls re-judged a task that had
been accepted in its previous judgement, 231 of them for an unchanged task
definition (57 definitions, up to 11 calls each), because later tasks kept
editing shared files. 28 of those calls flipped the verdict, and each flip was
a strike toward re-planning the whole project while other tasks were still
being implemented. The task is now held under review until no task is open,
and judged then, on the state the project will actually ship.
"""
import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from llmxive.agents import task_verifier as tv


@pytest.fixture(autouse=True)
def _receipt_key(monkeypatch) -> None:
    monkeypatch.setenv("LLMXIVE_RECEIPT_KEY", "ephemeral-test-final-state-key")


def _project(tmp_path: Path, second_mark: str = " ") -> tuple[Path, Path]:
    project = tmp_path / "projects/PROJ-914-final"
    (project / "data").mkdir(parents=True, exist_ok=True)
    tasks = project / "specs/001-study/tasks.md"
    tasks.parent.mkdir(parents=True, exist_ok=True)
    if not tasks.exists():
        (project / "data/a.txt").write_text("first\n", encoding="utf-8")
        (project / "data/b.txt").write_text("b\n", encoding="utf-8")
        tasks.write_text("- [X] T001 Write `data/a.txt`\n- [ ] T002 Write `data/b.txt`\n", encoding="utf-8")
    return project, tasks


def _pass(project: Path, tasks: Path) -> dict:
    memory = project / ".specify/memory"
    return tv.run_verification_pass(
        project, tasks, already_verified=tv.verified_done_keys(project, tasks),
        notes_path=memory / "task_verifier_notes.md", state_path=memory / "task_verify.yaml",
        project_id=project.name, repo_root=project.parent.parent)


def _judge(monkeypatch, complete: bool) -> list[str]:
    calls: list[str] = []

    def verdict(**kwargs):
        calls.append(kwargs["task_text"].split()[0])
        return SimpleNamespace(complete=complete, reason="judged", deferred=False)
    monkeypatch.setattr(tv, "verify_task", verdict)
    return calls


def _marks(tasks: Path) -> str:
    return "".join(line[3] for line in tasks.read_text(encoding="utf-8").splitlines())


def _kinds(project: Path) -> list[str]:
    ledger = project / ".specify/memory/task_verify.ledger.jsonl"
    return [json.loads(line)["kind"] for line in ledger.read_text(encoding="utf-8").splitlines()]


def test_a_changed_accepted_task_waits_while_another_task_is_open(tmp_path: Path, monkeypatch) -> None:
    project, tasks = _project(tmp_path)
    calls = _judge(monkeypatch, True)
    assert _pass(project, tasks)["accepted"] == 1 and calls == ["T001"]
    # A later task's work changes the accepted file. T002 is still open.
    (project / "data/a.txt").write_text("changed by another task\n", encoding="utf-8")
    calls.clear()
    monkeypatch.setattr(tv, "verify_task", lambda **k: pytest.fail("judged before the project settled"))
    result = _pass(project, tasks)
    assert result["deferred"] == ["T001"] and result["rejected"] == []
    assert _marks(tasks) == "~ "
    assert _kinds(project) == ["accepted", "postponed"]
    # Still waiting on the next pass; no strike is counted.
    assert _pass(project, tasks)["deferred"] == ["T001"]
    # T002 is claimed done: nothing is open, so both are judged on this state.
    tasks.write_text(tasks.read_text(encoding="utf-8").replace("- [ ] T002", "- [X] T002"), encoding="utf-8")
    calls = _judge(monkeypatch, True)
    assert _pass(project, tasks)["accepted"] == 2
    assert sorted(calls) == ["T001", "T002"] and _marks(tasks) == "XX"


def test_new_work_is_judged_at_once(tmp_path: Path, monkeypatch) -> None:
    project, tasks = _project(tmp_path)
    calls = _judge(monkeypatch, False)
    result = _pass(project, tasks)
    assert calls == ["T001"] and [key for key, _ in result["rejected"]] == ["T001"]


def test_a_missing_file_reopens_an_accepted_task_at_once(tmp_path: Path, monkeypatch) -> None:
    project, tasks = _project(tmp_path)
    _judge(monkeypatch, True)
    _pass(project, tasks)
    (project / "data/a.txt").unlink()
    monkeypatch.setattr(tv, "verify_task", lambda **k: pytest.fail("a missing file needs no model call"))
    result = _pass(project, tasks)
    assert [key for key, _ in result["rejected"]] == ["T001"] and _marks(tasks) == "  "


def test_an_unchanged_accepted_task_is_not_looked_at_again(tmp_path: Path, monkeypatch) -> None:
    project, tasks = _project(tmp_path)
    _judge(monkeypatch, True)
    _pass(project, tasks)
    monkeypatch.setattr(tv, "verify_task", lambda **k: pytest.fail("unchanged evidence"))
    result = _pass(project, tasks)
    assert result["deferred"] == [] and _marks(tasks) == "X "
