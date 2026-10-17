"""A reply that means "run it as it is" must not erase the script it names.

Canary 10 (2026-10-11): to re-run the analysis driver, the implementer sent

    - path: code/run_analysis.py
      execute: true
      contents: |
        # The file exists already; this entry requests execution without modification.

The comment was written over a 16 KB driver. Three tasks the verifier had
already accepted were then rejected ("run_analysis.py contains only a
comment"), and a later test was refused for importing ``main`` from a file
that no longer defined it. A few replies later the model added a second
``run_analysis.py`` at the project root to re-export the first.
"""
from pathlib import Path
from types import SimpleNamespace

import pytest
import yaml

from llmxive.backends.base import ChatResponse
from llmxive.project_files import has_code
from llmxive.speckit.implement_cmd import ImplementerAgent

DRIVER = (
    "from llmxive_toolkit import paths\n\n\n"
    "def main() -> int:\n"
    "    paths.data('summary.txt').write_text('ran\\n', encoding='utf-8')\n"
    "    return 0\n\n\n"
    "if __name__ == '__main__':\n"
    "    raise SystemExit(main())\n"
)
NOTE = "# The file exists already; this entry requests execution without modification.\n"
DOCSTRING_ONLY = '"""Unchanged; see the previous version."""\n'


def _send(tmp_path: Path, artifacts: list[dict]) -> Path:
    project = tmp_path / "projects/PROJ-909-noop"
    feature = project / "specs/001-study"
    feature.mkdir(parents=True, exist_ok=True)
    tasks = feature / "tasks.md"
    tasks.write_text("- [ ] T001 Run `code/run_analysis.py`\n", encoding="utf-8")
    document = {"task_id": "T001", "verdict": "completed", "artifacts": artifacts}
    ImplementerAgent().write_artifacts(
        SimpleNamespace(project_dir=project, project_id=project.name),
        {"tasks_path": str(tasks), "feature_dir": str(feature),
         "next_task_id": "T001", "all_complete": False},
        ChatResponse(text=yaml.safe_dump(document), model="test", backend="dartmouth"))
    return project


def _existing(tmp_path: Path, rel: str = "code/run_analysis.py", text: str = DRIVER) -> Path:
    target = tmp_path / "projects/PROJ-909-noop" / rel
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text(text, encoding="utf-8")
    return target


@pytest.mark.parametrize("contents", [NOTE, DOCSTRING_ONLY, "\n\n# unchanged\n"])
def test_a_comment_sent_with_execute_runs_the_script_that_is_there(tmp_path: Path, contents: str) -> None:
    driver = _existing(tmp_path)
    project = _send(tmp_path, [{"path": "code/run_analysis.py", "execute": True, "contents": contents}])
    assert driver.read_text(encoding="utf-8") == DRIVER
    assert (project / "data/summary.txt").read_text(encoding="utf-8") == "ran\n"
    log = (project / "code/.tasks/T001.code_run_analysis.py.log").read_text(encoding="utf-8")
    assert "(exit 0," in log
    assert "- [X] T001" in (project / "specs/001-study/tasks.md").read_text(encoding="utf-8")


def test_a_comment_sent_without_execute_is_refused(tmp_path: Path, capsys) -> None:
    driver = _existing(tmp_path)
    project = _send(tmp_path, [{"path": "code/run_analysis.py", "contents": NOTE}])
    assert driver.read_text(encoding="utf-8") == DRIVER
    assert "would replace working code with a file that has none" in capsys.readouterr().out
    assert "- [X] T001" not in (project / "specs/001-study/tasks.md").read_text(encoding="utf-8")


def test_a_shell_script_is_protected_the_same_way(tmp_path: Path) -> None:
    script = _existing(tmp_path, "code/run.sh", "#!/bin/sh\nset -e\necho ran > marker.txt\n")
    _send(tmp_path, [{"path": "code/run.sh", "contents": "#!/bin/sh\n# unchanged\n"}])
    assert "echo ran" in script.read_text(encoding="utf-8")


def test_a_real_rewrite_still_replaces_the_file(tmp_path: Path) -> None:
    driver = _existing(tmp_path)
    rewritten = DRIVER.replace("'ran\\n'", "'ran again\\n'")
    project = _send(tmp_path, [{"path": "code/run_analysis.py", "execute": True, "contents": rewritten}])
    assert driver.read_text(encoding="utf-8") == rewritten
    assert (project / "data/summary.txt").read_text(encoding="utf-8") == "ran again\n"


def test_a_file_with_no_code_to_lose_can_be_replaced_by_a_comment(tmp_path: Path) -> None:
    placeholder = _existing(tmp_path, "code/notes.py", "# to do\n")
    _send(tmp_path, [{"path": "code/notes.py", "contents": NOTE}])
    assert placeholder.read_text(encoding="utf-8") == NOTE


def test_a_root_level_duplicate_of_a_code_module_is_refused(tmp_path: Path, capsys) -> None:
    _existing(tmp_path)
    shim = "from code.run_analysis import main  # noqa: F401\n\n__all__ = ['main']\n"
    project = _send(tmp_path, [{"path": "run_analysis.py", "contents": shim}])
    assert not (project / "run_analysis.py").exists()
    assert "`code/run_analysis.py` already exists" in capsys.readouterr().out


def test_a_root_script_that_is_already_there_can_still_be_edited(tmp_path: Path) -> None:
    """Batch 7 run 1 (2026-10-12): the tests ran the root `run_phi_analysis.py`,
    a copy also sat in `code/`, and 44 edits to the root file were refused as
    "a second copy". Its one-line argument bug outlived three model tiers."""
    _existing(tmp_path)
    root = _existing(tmp_path, "run_analysis.py", DRIVER)
    rewritten = DRIVER.replace("'ran\\n'", "'root ran\\n'")
    project = _send(tmp_path, [{"path": "run_analysis.py", "contents": rewritten}])
    assert root.read_text(encoding="utf-8") == rewritten
    assert (project / "code/run_analysis.py").read_text(encoding="utf-8") == DRIVER


def test_a_script_sent_under_its_bare_name_is_written_to_the_one_that_exists(tmp_path: Path, capsys) -> None:
    """Batch 7 run 2: the task called the script `run_totient_analysis.py`, it
    lived in `code/`, and nine rewrites sent under the bare name were dropped."""
    driver = _existing(tmp_path)
    rewritten = DRIVER.replace("'ran\\n'", "'ran again\\n'")
    project = _send(tmp_path, [{"path": "run_analysis.py", "execute": True, "contents": rewritten}])
    assert not (project / "run_analysis.py").exists()
    assert driver.read_text(encoding="utf-8") == rewritten
    assert (project / "data/summary.txt").read_text(encoding="utf-8") == "ran again\n"
    assert "'run_analysis.py' -> 'code/run_analysis.py'" in capsys.readouterr().out


def test_a_bare_name_does_not_follow_a_link_out_of_the_project(tmp_path: Path) -> None:
    outside = tmp_path / "outside.py"
    outside.write_text(DRIVER, encoding="utf-8")
    link = tmp_path / "projects/PROJ-909-noop/code/run_analysis.py"
    link.parent.mkdir(parents=True)
    link.symlink_to(outside)
    _send(tmp_path, [{"path": "run_analysis.py", "contents": DRIVER.replace("ran", "overwritten")}])
    assert outside.read_text(encoding="utf-8") == DRIVER


@pytest.mark.parametrize("shim", [
    "import code.run_analysis as real\n\nmain = real.main\n",
    "from run_analysis import main\n\nraise SystemExit(main())\n",
    "import runpy\n\nrunpy.run_path('code/run_analysis.py', run_name='__main__')\n",
])
def test_a_wrapper_is_never_written_over_the_script_it_wraps(tmp_path: Path, shim: str) -> None:
    driver = _existing(tmp_path)
    project = _send(tmp_path, [{"path": "run_analysis.py", "contents": shim}])
    assert not (project / "run_analysis.py").exists()
    assert driver.read_text(encoding="utf-8") == DRIVER


def test_a_root_level_file_with_its_own_name_is_still_written(tmp_path: Path) -> None:
    _existing(tmp_path)
    project = _send(tmp_path, [{"path": "requirements.txt", "contents": "numpy\n"}])
    assert (project / "requirements.txt").read_text(encoding="utf-8") == "numpy\n"


@pytest.mark.parametrize("name,text,expected", [
    ("a.py", DRIVER, True), ("a.py", NOTE, False), ("a.py", DOCSTRING_ONLY, False), ("a.py", "", False),
    ("a.py", "X = 1\n", True), ("a.py", "def broken(:\n", True),
    ("a.sh", "#!/bin/sh\n# note\n\n", False), ("a.sh", "#!/bin/sh\necho hi\n", True),
    ("a.md", "# Heading\n", True), ("a.csv", "", False),
])
def test_what_counts_as_code(name: str, text: str, expected: bool) -> None:
    assert has_code(name, text) is expected
