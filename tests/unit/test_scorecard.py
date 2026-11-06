"""Every executed check and every verdict becomes a number with a history.

Reliability batch 1 (2026-10-11), rebuilt after the fact from the verifier's
saved calls: 26 of 61 accepted tasks were later rejected, and the pipeline had
no record of which check had changed. These tests drive the real implementer
and the real verification pass and read what they recorded.
"""
from pathlib import Path
from types import SimpleNamespace

import yaml

from llmxive.backends.base import ChatResponse
from llmxive.speckit import scorecard
from llmxive.speckit.implement_cmd import ImplementerAgent

GOOD = "from llmxive_toolkit import paths\npaths.data('n.txt').write_text('3\\n', encoding='utf-8')\n"
BAD = "raise SystemExit(4)\n"
TESTS = (
    "from pathlib import Path\n"
    "def test_value():\n    assert Path('data/n.txt').read_text().strip() == '3'\n"
    "def test_wrong():\n    assert 1 == 2\n"
)


def _send(tmp_path: Path, task_id: str, path: str, contents: str) -> Path:
    project = tmp_path / "projects/PROJ-913-scorecard"
    feature = project / "specs/001-study"
    feature.mkdir(parents=True, exist_ok=True)
    tasks = feature / "tasks.md"
    tasks.write_text("- [ ] T001 Write `data/n.txt`\n- [ ] T002 Test it\n", encoding="utf-8")
    document = {"task_id": task_id, "verdict": "completed",
                "artifacts": [{"path": path, "execute": True, "contents": contents}]}
    ImplementerAgent().write_artifacts(
        SimpleNamespace(project_dir=project, project_id=project.name),
        {"tasks_path": str(tasks), "feature_dir": str(feature),
         "next_task_id": task_id, "all_complete": False},
        ChatResponse(text=yaml.safe_dump(document), model="test", backend="dartmouth"))
    return project / ".specify/memory"


def test_a_run_records_its_exit_as_a_number(tmp_path: Path) -> None:
    memory = _send(tmp_path, "T001", "code/make.py", GOOD)
    assert scorecard.current(memory, "T001") == {"run:code/make.py": 1}
    _send(tmp_path, "T001", "code/make.py", BAD)
    assert scorecard.current(memory, "T001") == {"run:code/make.py": 0}
    assert [row["values"]["run:code/make.py"] for row in scorecard.history(memory, "T001")] == [1, 0]


def test_a_test_module_records_one_number_per_test(tmp_path: Path) -> None:
    _send(tmp_path, "T001", "code/make.py", GOOD)
    memory = _send(tmp_path, "T002", "tests/test_n.py", TESTS)
    assert scorecard.current(memory, "T002") == {
        "run:tests/test_n.py": 0,
        "test:tests/test_n.py::test_value": 1,
        "test:tests/test_n.py::test_wrong": 0,
    }
    # Another task's numbers are its own.
    assert scorecard.current(memory, "T001") == {"run:code/make.py": 1}


def test_arguments_and_the_task_definition_are_part_of_the_record(tmp_path: Path) -> None:
    from llmxive.agents.task_verifier import definition_signatures

    project = tmp_path / "projects/PROJ-913-scorecard"
    feature = project / "specs/001-study"
    feature.mkdir(parents=True)
    tasks = feature / "tasks.md"
    memory = project / ".specify/memory"

    def send(args: list) -> None:
        document = {"task_id": "T001", "verdict": "completed", "artifacts": [
            {"path": "code/make.py", "execute": True, "args": args,
             "contents": "import sys\nraise SystemExit(0 if sys.argv[1:] == ['--n', '3'] else 2)\n"}]}
        ImplementerAgent().write_artifacts(
            SimpleNamespace(project_dir=project, project_id=project.name),
            {"tasks_path": str(tasks), "feature_dir": str(feature), "next_task_id": "T001", "all_complete": False},
            ChatResponse(text=yaml.safe_dump(document), model="test", backend="dartmouth"))

    tasks.write_text("- [ ] T001 Run `code/make.py --n 3`\n", encoding="utf-8")
    first = definition_signatures(tasks.read_text(encoding="utf-8"))["T001"]
    send(["--n", 3])
    send(["--n", 4])
    assert scorecard.current(memory, "T001") == {"run:code/make.py --n 3": 1, "run:code/make.py --n 4": 0}
    # A re-plan gives the id to other work: its history starts empty.
    tasks.write_text("- [ ] T001 Run `code/make.py --n 4` instead\n", encoding="utf-8")
    second = definition_signatures(tasks.read_text(encoding="utf-8"))["T001"]
    assert first != second
    send(["--n", 4])
    assert scorecard.current(memory, "T001", definition=second) == {"run:code/make.py --n 4": 0}
    assert len(scorecard.history(memory, "T001", definition=first)) == 2


def test_delta_counts_only_measured_changes() -> None:
    before = {"run:a.py": 1, "test:t::x": 0, "test:t::y": 1, "judge": None}
    after = {"run:a.py": 0, "test:t::x": 1, "test:t::y": 1, "test:t::new": 0, "judge": 1}
    assert scorecard.delta(before, after) == (["test:t::x"], ["run:a.py"])


def test_a_torn_last_line_is_skipped(tmp_path: Path) -> None:
    scorecard.record(tmp_path, "T001", "run", {"run:a.py": 1})
    with scorecard.scorecard_path(tmp_path).open("a", encoding="utf-8") as stream:
        stream.write('{"at": "2026-10-11T00:00:00+00:00", "task": "T001", "val')
    assert scorecard.current(tmp_path, "T001") == {"run:a.py": 1}
    assert scorecard.history(tmp_path / "absent") == []


def test_the_verifier_records_its_verdict_and_missing_files(tmp_path: Path, monkeypatch) -> None:
    from llmxive.agents import task_verifier

    project = tmp_path / "projects/PROJ-913-scorecard"
    memory = project / ".specify/memory"
    tasks = project / "specs/001-study/tasks.md"
    tasks.parent.mkdir(parents=True)
    (project / "data").mkdir()
    (project / "data/n.txt").write_text("3\n", encoding="utf-8")
    tasks.write_text("- [X] T001 Write `data/n.txt`\n- [X] T002 Write `data/absent.csv`\n", encoding="utf-8")
    monkeypatch.setattr(task_verifier, "verify_task", lambda *a, **k: task_verifier.TaskVerdict(False, "the value is wrong"))
    task_verifier.run_verification_pass(
        project, tasks, already_verified=set(), project_id=project.name, repo_root=tmp_path,
        notes_path=memory / "task_verifier_notes.md", state_path=memory / "task_verify.yaml")
    assert scorecard.current(memory, "T001") == {"judge": 0}
    assert scorecard.current(memory, "T002") == {"files": 0}
    monkeypatch.setattr(task_verifier, "verify_task", lambda *a, **k: task_verifier.TaskVerdict(True, "ok"))
    (project / "data/n.txt").write_text("4\n", encoding="utf-8")
    tasks.write_text(tasks.read_text(encoding="utf-8").replace("- [ ] T001", "- [X] T001"), encoding="utf-8")
    task_verifier.run_verification_pass(
        project, tasks, already_verified=set(), project_id=project.name, repo_root=tmp_path,
        notes_path=memory / "task_verifier_notes.md", state_path=memory / "task_verify.yaml")
    assert [row["values"] for row in scorecard.history(memory, "T001")] == [{"judge": 0}, {"judge": 1}]
