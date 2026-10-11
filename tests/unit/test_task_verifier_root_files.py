"""A file a task names at the project root is evidence.

Canary 6 (2026-10-11), T015: "add a `README.md` entry at the project root
linking to `data/paper.md`". The README existed and had the entry. Only
`data/paper.md` was quoted to the verifier, which rejected the task because
"the evidence list contains no `README.md` file at the project root".
"""
from pathlib import Path

import pytest

from llmxive.agents import task_verifier
from llmxive.project_paths import declared_root_files

TASK = ("T015 Paper-stage hand-off - add a `README.md` entry at the project root "
        "linking to `data/paper.md`.")


@pytest.fixture
def project(tmp_path: Path) -> Path:
    project = tmp_path / "projects/PROJ-907-root"
    (project / "data").mkdir(parents=True)
    (project / "data/paper.md").write_text("# Paper\n\nResults.\n", encoding="utf-8")
    (project / "README.md").write_text(
        "# Methods & Results\n\nSee [the draft](data/paper.md).\n", encoding="utf-8")
    return project


def test_a_named_project_root_file_is_quoted(project: Path) -> None:
    evidence = task_verifier.gather_evidence(project, TASK)
    assert "- `README.md` (resolved: `README.md`" in evidence
    assert "See [the draft](data/paper.md)." in evidence


def test_only_names_that_exist_at_the_root_are_added(project: Path) -> None:
    text = ("T001 Use `scipy.stats`, call `json.dump`, write `notes.md`, run `run_all.sh`, "
            "update `README.md` and `data/paper.md`, and keep `paper.md` in sync.")
    (project / "run_all.sh").write_text("#!/bin/bash\n", encoding="utf-8")
    # `notes.md` does not exist; `paper.md` exists only under data/, not at the root.
    assert declared_root_files(project, text) == ["run_all.sh", "README.md"]


def test_a_name_already_declared_as_a_path_is_not_repeated(project: Path) -> None:
    (project / "requirements.txt").write_text("numpy==1.26.4\n", encoding="utf-8")
    text = "T000 Pin dependencies in `requirements.txt`."
    assert declared_root_files(project, text) == []
    assert task_verifier.gather_evidence(project, text).count("- `requirements.txt` (resolved") == 1


def test_a_root_file_does_not_escape_the_project(project: Path, tmp_path: Path) -> None:
    (tmp_path / "secret.md").write_text("outside", encoding="utf-8")
    (project / "link.md").symlink_to(tmp_path / "secret.md")
    assert declared_root_files(project, "T002 Read `link.md`.") == []
