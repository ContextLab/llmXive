"""A test module the implementer writes is run by pytest, and the verifier sees it.

Canary 7 (2026-10-11) had two test tasks rejected with "no evidence pytest was
run". One reply executed a wrapper that sent pytest's output to a file the
verifier never reads; the other's test passed inside a shell script but imported
``llmxive_toolkit``, which the verifier took for a missing project file.
"""
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from llmxive import sandbox
from llmxive.agents import task_verifier
from llmxive.backends.base import ChatResponse
from llmxive.speckit.implement_cmd import ImplementerAgent

LIB = "def double(x):\n    return 2 * x\n"
PASSING = (
    "from llmxive_toolkit import paths\n"
    "from lib import double\n\n\n"
    "def test_double():\n"
    "    assert paths.root.is_dir()\n"
    "    assert double(21) == 42\n"
)
FAILING = "def test_arithmetic():\n    assert 1 + 1 == 3\n"


def _run(tmp_path: Path, artifacts: list[dict], task: str = "Write tests/test_lib.py") -> Path:
    project = tmp_path / "projects/PROJ-902-tests"
    feature = project / "specs/001-study"
    feature.mkdir(parents=True, exist_ok=True)
    tasks = feature / "tasks.md"
    tasks.write_text(f"- [ ] T001 {task}\n", encoding="utf-8")
    document = {"task_id": "T001", "verdict": "completed", "artifacts": artifacts}
    ImplementerAgent().write_artifacts(
        SimpleNamespace(project_dir=project, project_id=project.name),
        {"tasks_path": str(tasks), "feature_dir": str(feature),
         "next_task_id": "T001", "all_complete": False},
        ChatResponse(text=yaml.safe_dump(document), model="test", backend="dartmouth"))
    return project


def _log(project: Path, relpath: str = "tests/test_lib.py") -> str:
    return (project / "code/.tasks" / f"T001.{relpath.replace('/', '_')}.log").read_text(encoding="utf-8")


def test_a_written_test_module_is_run_by_pytest_without_being_asked(tmp_path: Path) -> None:
    project = _run(tmp_path, [
        {"path": "code/lib.py", "contents": LIB},
        {"path": "tests/test_lib.py", "contents": PASSING},
    ])
    log = _log(project)
    assert "# tests/test_lib.py (exit 0," in log
    assert "tests/test_lib.py::test_double PASSED" in log
    assert "1 passed" in log
    assert "- [X] T001" in (project / "specs/001-study/tasks.md").read_text(encoding="utf-8")
    # The run leaves no cache directory behind in the project.
    assert not list(project.rglob(".pytest_cache"))


def test_execute_true_on_a_test_module_means_pytest_not_plain_python(tmp_path: Path) -> None:
    """``python tests/test_x.py`` exits 0 having collected nothing."""
    project = _run(tmp_path, [{"path": "tests/test_lib.py", "contents": FAILING, "execute": True}])
    log = _log(project)
    assert "test_arithmetic FAILED" in log and "1 failed" in log
    tasks = (project / "specs/001-study/tasks.md").read_text(encoding="utf-8")
    assert "FAILED-IN-EXECUTION: tests/test_lib.py exit=1" in tasks
    assert "- [X] T001" not in tasks


def test_an_unrequested_failing_test_is_evidence_not_a_failed_command(tmp_path: Path) -> None:
    """A task may write a test before the code under test exists."""
    project = _run(tmp_path, [{"path": "tests/test_lib.py", "contents": FAILING}])
    assert "1 failed" in _log(project)
    tasks = (project / "specs/001-study/tasks.md").read_text(encoding="utf-8")
    assert "FAILED-IN-EXECUTION" not in tasks and "- [X] T001" in tasks


def test_the_verifier_is_shown_the_pytest_session_and_the_toolkit_note(tmp_path: Path) -> None:
    project = _run(tmp_path, [
        {"path": "code/lib.py", "contents": LIB},
        {"path": "tests/test_lib.py", "contents": PASSING},
    ])
    evidence = task_verifier.gather_evidence(project, "T001 Write `tests/test_lib.py` and run it with pytest")
    assert "tests/test_lib.py::test_double PASSED" in evidence
    assert "python -m pytest -v" in evidence
    assert "installed by the platform on every project's import path" in evidence


def test_the_toolkit_note_is_absent_when_nothing_imports_it(tmp_path: Path) -> None:
    project = tmp_path / "projects/PROJ-903-plain"
    (project / "code").mkdir(parents=True)
    (project / "code/lib.py").write_text(LIB, encoding="utf-8")
    evidence = task_verifier.gather_evidence(project, "T001 Write `code/lib.py`")
    assert "llmxive_toolkit" not in evidence


@pytest.mark.parametrize("relpath, problem", [
    ("../outside/test_x.py", "escapes the project"),
    ("tests/test_absent.py", "not found"),
])
def test_a_test_path_outside_or_missing_is_refused_without_running(tmp_path, relpath, problem) -> None:
    project = tmp_path / "projects/PROJ-904-paths"
    project.mkdir(parents=True)
    result = sandbox.run_pytest_file(project_dir=project, test_relpath=relpath)
    assert not result.ok and problem in result.stderr
    assert not sandbox.venv_dir(project).exists()


@pytest.mark.parametrize("name, expected", [
    ("test_sieve.py", True), ("sieve_test.py", True), ("conftest.py", False),
    ("run_test_sieve.py", False), ("test_notes.md", False), ("testing.py", False),
])
def test_pytest_module_names(name: str, expected: bool) -> None:
    from llmxive.project_files import is_pytest_module

    assert is_pytest_module(name) is expected
