"""A task list naming a platform-owned path is refused where it is written."""
from pathlib import Path

import pytest

from llmxive.execution.platform_paths import (
    platform_path_tasks,
    project_dir_of,
    refuse_platform_path_tasks,
)
from llmxive.speckit._legacy_guards import check_legacy_guards
from llmxive.speckit.task_lines import TaskFormatError

TASKS = """# Tasks

- [ ] T001 Implement the sieve in `code/sieve.py`.
- [X] T002 Earlier workflow `.github/workflows/old.yml`.
- [ ] T003 Write the tests in `tests/test_sieve.py`.
- [ ] T004 Record the run in `data/state/run.json`.
- [ ] T012 [P] CI workflow - add GitHub Actions file that:
  - lives at `.github/workflows/phi.yml`
  - runs `pytest -q`
- [~] T013 Save the hashes under `state/hashes.json`.
"""


def test_unfinished_tasks_naming_platform_paths_are_listed():
    assert platform_path_tasks(TASKS) == [
        ("T012", ".github/workflows/phi.yml", ".github"),
        ("T013", "state/hashes.json", "state"),
    ]


def test_a_project_task_list_with_a_workflow_file_is_refused(tmp_path):
    project = tmp_path / "projects" / "PROJ-9999-totient-canary"
    with pytest.raises(TaskFormatError) as refused:
        refuse_platform_path_tasks(TASKS, project)
    message = str(refused.value)
    assert "T012 `.github/workflows/phi.yml`" in message
    assert "T013 `state/hashes.json`" in message
    assert "T002" not in message and "T004" not in message
    assert "scripts/" in message


def test_the_rule_is_for_projects_only(tmp_path):
    refuse_platform_path_tasks(TASKS, None)
    refuse_platform_path_tasks(TASKS, tmp_path / "specs" / "025-self-improvement-lane")


def test_a_revised_task_list_cannot_bring_the_path_back(tmp_path):
    project = tmp_path / "projects" / "PROJ-9999-totient-canary"
    padded = TASKS + "".join(f"- [ ] T1{n:02d} Step {n} in `code/step{n}.py`.\n" for n in range(5))
    refusals = check_legacy_guards(
        filename="tasks.md", new_content=padded, original_content="", project_dir=project)
    assert len(refusals) == 1 and ".github/workflows/phi.yml" in refusals[0]
    clean = padded.replace(".github/workflows/phi.yml", "scripts/ci.sh").replace(
        "state/hashes.json", "data/hashes.json")
    assert check_legacy_guards(
        filename="tasks.md", new_content=clean, original_content="", project_dir=project) == []


@pytest.mark.parametrize("path,expected", [
    ("projects/PROJ-1-a/specs/001-x/tasks.md", Path("projects/PROJ-1-a")),
    ("/repo/projects/PROJ-1-a/specs/001-x/tasks.md", Path("/repo/projects/PROJ-1-a")),
    ("specs/025-lane/tasks.md", None),
    ("projects", None),
])
def test_project_dir_of(path, expected):
    assert project_dir_of(path) == expected


def test_the_implementer_stops_on_such_a_task_instead_of_attempting_it(tmp_path):
    """An existing project routes back to the tasker with the reason (the
    graph turns this error into re-plan feedback) rather than spending rounds."""
    from types import SimpleNamespace

    from llmxive.speckit.implement_cmd import ImplementerAgent

    (tmp_path / "agents").symlink_to(Path(__file__).resolve().parents[2] / "agents")
    project = tmp_path / "projects" / "PROJ-9999-totient-canary"
    feature = project / "specs" / "001-study"
    feature.mkdir(parents=True)
    (feature / "spec.md").write_text("Count totient residues.\n")
    (feature / "tasks.md").write_text(TASKS)
    ctx = SimpleNamespace(project_dir=project, project_id=project.name)
    with pytest.raises(TaskFormatError, match=r"T012 `\.github/workflows/phi\.yml`"):
        ImplementerAgent().mechanical_step(ctx)
