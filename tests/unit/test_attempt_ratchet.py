"""An attempt that breaks a passing test is undone; any other attempt is kept.

Reliability batch 1 (2026-10-11): none of the 13 retries that made a passing
executed check fail was later accepted, and 25 of the 39 accepted retries
changed no executed check at all. These tests drive the real implementer, the
real sandbox and real pytest sessions.
"""
from pathlib import Path
from types import SimpleNamespace

import yaml

from llmxive.backends.base import ChatResponse
from llmxive.speckit import ratchet, scorecard
from llmxive.speckit.implement_cmd import ImplementerAgent

LIB = "def total(values):\n    return sum(values)\n"
BROKEN_LIB = "def total(values):\n    return 0\n"
TESTS = (
    "import sys\nsys.path.insert(0, 'code')\nfrom lib import total\n\n"
    "def test_total():\n    assert total([1, 2, 3]) == 6\n\n"
    "def test_empty():\n    assert total([]) == 0\n"
)
TASKS = (
    "- [ ] T001 Write `code/lib.py`\n- [ ] T002 Test it in `tests/test_lib.py`\n"
    "- [ ] T003 Write `data/note.txt`\n"
)


def _send(tmp_path: Path, task_id: str, artifacts: list[dict]) -> Path:
    project = tmp_path / "projects/PROJ-915-ratchet"
    feature = project / "specs/001-study"
    feature.mkdir(parents=True, exist_ok=True)
    tasks = feature / "tasks.md"
    if not tasks.exists():
        tasks.write_text(TASKS, encoding="utf-8")
    document = {"task_id": task_id, "verdict": "completed", "artifacts": artifacts}
    ImplementerAgent().write_artifacts(
        SimpleNamespace(project_dir=project, project_id=project.name),
        {"tasks_path": str(tasks), "feature_dir": str(feature),
         "next_task_id": task_id, "all_complete": False},
        ChatResponse(text=yaml.safe_dump(document), model="test", backend="dartmouth"))
    return project


def _start(tmp_path: Path) -> Path:
    _send(tmp_path, "T001", [{"path": "code/lib.py", "contents": LIB}])
    return _send(tmp_path, "T002", [{"path": "tests/test_lib.py", "contents": TESTS}])


def _line(project: Path, task_id: str) -> str:
    text = (project / "specs/001-study/tasks.md").read_text(encoding="utf-8")
    return next(line for line in text.splitlines() if task_id in line)


def test_an_attempt_that_breaks_a_passing_test_is_undone(tmp_path: Path) -> None:
    project = _start(tmp_path)
    _send(tmp_path, "T003", [
        {"path": "code/lib.py", "contents": BROKEN_LIB},
        {"path": "data/note.txt", "contents": "written by the attempt\n"},
    ])
    # Every file is back as it was, and what the attempt added is gone.
    assert (project / "code/lib.py").read_text(encoding="utf-8") == LIB
    assert not (project / "data/note.txt").exists()
    # The task is marked the way a failed command is, naming the test module.
    assert _line(project, "T003") == (
        "- [~] T003 Write `data/note.txt` <!-- FAILED-IN-EXECUTION: tests/test_lib.py exit=1 -->")
    assert _line(project, "T002").startswith("- [X] T002")
    record = (project / "code/.tasks/T003.attempt-not-kept.log").read_text(encoding="utf-8")
    assert "- `tests/test_lib.py::test_total`" in record and "test_empty" not in record.split("## files")[0]
    assert "- `code/lib.py`" in record and "- `data/note.txt`" in record
    assert "assert 0 == 6" in record
    memory = project / ".specify/memory"
    assert scorecard.current(memory, "T003") == {"kept": 0}


def test_an_attempt_that_breaks_nothing_is_kept(tmp_path: Path) -> None:
    project = _start(tmp_path)
    _send(tmp_path, "T003", [{"path": "data/note.txt", "contents": "kept\n"}])
    assert (project / "data/note.txt").read_text(encoding="utf-8") == "kept\n"
    assert _line(project, "T003").startswith("- [X] T003")
    assert scorecard.current(project / ".specify/memory", "T003") == {"kept": 1}
    assert not (project / "code/.tasks/T003.attempt-not-kept.log").exists()


def test_a_test_that_already_failed_does_not_block_an_attempt(tmp_path: Path) -> None:
    _send(tmp_path, "T001", [{"path": "code/lib.py", "contents": BROKEN_LIB}])
    project = _send(tmp_path, "T002", [{"path": "tests/test_lib.py", "contents": TESTS}])
    # test_total fails before the attempt; the attempt fixes the library.
    _send(tmp_path, "T003", [{"path": "code/lib.py", "contents": LIB}])
    assert (project / "code/lib.py").read_text(encoding="utf-8") == LIB
    assert scorecard.current(project / ".specify/memory", "T003") == {"kept": 1}


def test_rewriting_a_test_module_may_rename_tests_but_not_lose_passing_ones(tmp_path: Path) -> None:
    project = _start(tmp_path)
    renamed = TESTS.replace("test_total", "test_sum_of_three")
    _send(tmp_path, "T003", [{"path": "tests/test_lib.py", "contents": renamed}])
    assert (project / "tests/test_lib.py").read_text(encoding="utf-8") == renamed
    fewer = renamed.split("def test_empty")[0]
    _send(tmp_path, "T003", [{"path": "tests/test_lib.py", "contents": fewer}])
    assert (project / "tests/test_lib.py").read_text(encoding="utf-8") == renamed
    record = (project / "code/.tasks/T003.attempt-not-kept.log").read_text(encoding="utf-8")
    assert "`tests/test_lib.py (2 tests passed before this attempt, 1 pass after it)`" in record


def test_regressions_is_a_set_comparison() -> None:
    before = {"t.py::a": 1, "t.py::b": 0, "u.py::c": 1, "u.py::d": 1}
    assert ratchet.regressions(before, dict(before), set()) == []
    assert ratchet.regressions(before, {**before, "t.py::a": 0, "t.py::b": 1}, set()) == ["t.py::a"]
    # A passing test that vanished from a module the attempt did not rewrite.
    assert ratchet.regressions(before, {"t.py::a": 1, "t.py::b": 0, "u.py::c": 1}, set()) == ["u.py::d"]
    # A rewritten module is judged on how many of its tests pass.
    assert ratchet.regressions(before, {"t.py::a": 1, "u.py::x": 1, "u.py::y": 1}, {"u.py"}) == []
    assert ratchet.regressions(before, {"t.py::a": 1, "u.py::x": 1}, {"u.py"}) == [
        "u.py (2 tests passed before this attempt, 1 pass after it)"]


def test_a_project_without_tests_or_a_paper_task_is_not_guarded(tmp_path: Path) -> None:
    project = _send(tmp_path, "T001", [{"path": "code/lib.py", "contents": LIB}])
    assert scorecard.history(project / ".specify/memory") == []
    _send(tmp_path, "T002", [{"path": "tests/test_lib.py", "contents": TESTS}])
    assert ratchet.begin(project, "T009", project / "paper/.specify/memory", "", log_dir="paper/.tasks") is None


def test_the_mark_of_an_undone_attempt_goes_when_a_later_attempt_is_kept(tmp_path: Path) -> None:
    """Batch 3 runs 2 and 5 (2026-10-11): the mark named a test module the task
    did not own and that passed again once the files were restored. No reply
    could "rerun it successfully", so the verifier rejected the task unjudged
    on every later round (15 such rejections) until it was called unverifiable."""
    project = _start(tmp_path)
    _send(tmp_path, "T003", [
        {"path": "code/lib.py", "contents": BROKEN_LIB},
        {"path": "data/note.txt", "contents": "written by the attempt\n"},
    ])
    assert "FAILED-IN-EXECUTION: tests/test_lib.py exit=1" in _line(project, "T003")
    _send(tmp_path, "T003", [{"path": "data/note.txt", "contents": "written by the attempt\n"}])
    line = _line(project, "T003")
    assert "FAILED-IN-EXECUTION" not in line
    assert line.startswith("- [X] T003")


def test_a_task_that_fails_its_own_test_keeps_its_work_and_is_marked(tmp_path: Path) -> None:
    """Batch 3 run 2 T005: the task's own test passed only because of a branch
    the verifier called fabricated. Six replies removed the branch, the test
    then failed, and each was undone, so the work the verifier asked for never
    reached it. A task's own failing test is a result to report, not a
    regression in someone else's work."""
    project = _start(tmp_path)
    _send(tmp_path, "T002", [{"path": "code/lib.py", "contents": BROKEN_LIB}])
    assert (project / "code/lib.py").read_text(encoding="utf-8") == BROKEN_LIB
    assert not (project / "code/.tasks/T002.attempt-not-kept.log").exists()
    line = _line(project, "T002")
    assert line.startswith("- [~] T002")
    assert "FAILED-IN-EXECUTION: tests/test_lib.py exit=1" in line

    _send(tmp_path, "T002", [{"path": "code/lib.py", "contents": LIB}])
    line = _line(project, "T002")
    assert "FAILED-IN-EXECUTION" not in line
    assert line.startswith("- [X] T002")


def test_a_test_module_two_tasks_ran_belongs_to_neither(tmp_path: Path) -> None:
    logs = tmp_path / "code/.tasks"
    logs.mkdir(parents=True)
    (logs / "T002.tests_test_lib.py.log").write_text("# tests/test_lib.py (exit 0, 0.1s, ok=True)\n")
    (logs / "T002.tests_unit_test_io.py.log").write_text("# tests/unit/test_io.py (exit 0, 0.1s, ok=True)\n")
    (logs / "T004.tests_unit_test_io.py.log").write_text("# tests/unit/test_io.py (exit 0, 0.1s, ok=True)\n")
    modules = ["tests/test_lib.py", "tests/unit/test_io.py", "tests/test_other.py"]
    assert ratchet.own_modules(tmp_path, "T002", modules, "code/.tasks") == {"tests/test_lib.py"}
    assert ratchet.own_modules(tmp_path, "T004", modules, "code/.tasks") == set()


CLOBBERING_TEST = (
    "import shutil\nfrom pathlib import Path\n\n"
    "def test_small_run():\n"
    "    Path('data/summary.csv').write_text('n,tv\\n10,0.5\\n')\n"
    "    Path('data/stray_n10.csv').write_text('x\\n')\n"
    "    shutil.rmtree('figures')\n"
    "    assert True\n"
)
FULL = "n,tv\n1000,0.1\n10000,0.05\n"


def _results(project: Path) -> dict[str, str]:
    return {path.relative_to(project).as_posix(): path.read_text(encoding="utf-8")
            for folder in ("data", "figures") for path in sorted((project / folder).rglob("*")) if path.is_file()}


def test_a_test_session_cannot_replace_or_remove_another_tasks_results(tmp_path: Path) -> None:
    """Batches 4 and 5: tests rewrote ``tv_summary.csv`` with one row and removed ``results/``."""
    project = _start(tmp_path)
    _send(tmp_path, "T003", [
        {"path": "data/summary.csv", "contents": FULL},
        {"path": "figures/plot.txt", "contents": "the figure\n"},
        {"path": "data/note.txt", "contents": "note\n"},
    ])
    expected = _results(project)
    assert expected["data/summary.csv"] == FULL

    # The implementer writes the test: the runtime runs it at once.
    _send(tmp_path, "T002", [{"path": "tests/test_small.py", "contents": CLOBBERING_TEST}])
    log = (project / "code/.tasks/T002.tests_test_small.py.log").read_text(encoding="utf-8")
    assert "test_small_run PASSED" in log
    assert _results(project) == expected

    # Every later attempt runs all tests before and after it.
    _send(tmp_path, "T003", [{"path": "data/note.txt", "contents": "a later attempt\n"}])
    expected["data/note.txt"] = "a later attempt\n"
    assert _results(project) == expected


def test_files_unchanged_puts_back_changed_removed_and_new_files(tmp_path: Path) -> None:
    (tmp_path / "data").mkdir()
    (tmp_path / "data/a.csv").write_text("full\n", encoding="utf-8")
    (tmp_path / "data/b.csv").write_text("kept\n", encoding="utf-8")
    try:
        with ratchet.files_unchanged(tmp_path):
            (tmp_path / "data/a.csv").write_text("x\n", encoding="utf-8")
            (tmp_path / "data/b.csv").unlink()
            (tmp_path / "data/new.csv").write_text("stray\n", encoding="utf-8")
            raise RuntimeError("the session failed")
    except RuntimeError:
        pass
    assert sorted(p.name for p in (tmp_path / "data").iterdir()) == ["a.csv", "b.csv"]
    assert (tmp_path / "data/a.csv").read_text(encoding="utf-8") == "full\n"
