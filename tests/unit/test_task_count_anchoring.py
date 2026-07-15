"""Task-completion counting must match REAL task lines, not any `- [ ]` substring.

`_all_tasks_done` checked `"[ ]" not in text` and `_incomplete_task_count` used
`text.count("- [ ]")`. A tasks.md whose HEADER documents the task format —

    ## Format: `- [ ] T### [P?] [Story] Description (file path)`

— contains the literal `- [ ]` as an EXAMPLE, so those functions counted 1 phantom
incomplete task even with all 60 real tasks checked off. `_all_tasks_done` stayed
False forever, so the execution gate NEVER ran and the project sat at in_progress
untouched for 16 days (PROJ-148). Counting must key on real checkbox LINES.
"""

from __future__ import annotations

from pathlib import Path

from llmxive.pipeline import graph
from llmxive.state import project as project_store


def _proj(tmp_path: Path, tasks_body: str) -> Path:
    pid = "PROJ-148-x"
    d = tmp_path / "projects" / pid / "specs" / "001-x"
    d.mkdir(parents=True)
    (d / "tasks.md").write_text(tasks_body, encoding="utf-8")
    # point the SSoT feature-dir resolver at it
    (tmp_path / "state" / "projects").mkdir(parents=True, exist_ok=True)
    return tmp_path / "projects" / pid


_FORMAT_HEADER = "## Format: `- [ ] T### [P?] [Story] Description (file path)`\n\n"


def test_format_header_example_is_not_an_incomplete_task(tmp_path: Path) -> None:
    body = _FORMAT_HEADER + "- [X] T001 Do the thing (code/x.py)\n- [X] T002 Do more\n"
    proj = _proj(tmp_path, body)
    assert graph._incomplete_task_count(proj, paper=False) == 0, (
        "the `- [ ]` inside the format-doc header was counted as a real open task"
    )
    assert graph._all_tasks_done(proj) is True, (
        "all real tasks are [X]; the format-doc example must not block completion"
    )


def test_real_open_task_still_counts(tmp_path: Path) -> None:
    body = _FORMAT_HEADER + "- [X] T001 done\n- [ ] T002 not done yet\n"
    proj = _proj(tmp_path, body)
    assert graph._incomplete_task_count(proj, paper=False) == 1
    assert graph._all_tasks_done(proj) is False


def test_under_review_task_still_counts(tmp_path: Path) -> None:
    body = _FORMAT_HEADER + "- [X] T001 done\n- [~] T002 under review\n"
    proj = _proj(tmp_path, body)
    assert graph._incomplete_task_count(proj, paper=False) == 1
    assert graph._all_tasks_done(proj) is False


def test_indented_subtask_checkbox_is_counted(tmp_path: Path) -> None:
    """A genuinely-indented open checkbox IS a real task and must still count
    (the fix keys on line-anchored checkbox lines, which allow leading whitespace)."""
    body = "- [X] T001 parent\n  - [ ] T001a real indented subtask\n"
    proj = _proj(tmp_path, body)
    assert graph._incomplete_task_count(proj, paper=False) == 1
    assert graph._all_tasks_done(proj) is False


def test_empty_tasks_file_is_not_done(tmp_path: Path) -> None:
    proj = _proj(tmp_path, "# Tasks\n\nNo checkboxes here.\n")
    assert graph._all_tasks_done(proj) is False
