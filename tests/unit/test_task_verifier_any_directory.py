"""A file a task names is evidence whatever its directory is called.

Canary 10 (2026-10-11): the tasks wrote `output/tv_table.md`,
`output/tv_vs_N.png` and `output/paper.md`. All three existed. The evidence
collector recognised a fixed list of directory names that had `outputs` but not
`output`, so none was shown to the verifier, which rejected T007 and T008 three
times each ("the required artifacts ... are not present nor shown") and sent
the project to full revision.
"""
from pathlib import Path

import pytest

from llmxive.agents import task_verifier
from llmxive.project_paths import declared_existing_files, declared_paths

TASK = ("T008 Generate `output/paper.md` programmatically from `data/summary.json`, "
        "referencing `output/tv_table.md` and `tables/extra/tv_long.md`.")


@pytest.fixture
def project(tmp_path: Path) -> Path:
    project = tmp_path / "projects/PROJ-910-output"
    for rel, text in {
        "data/summary.json": '{"rows": 12}\n',
        "output/paper.md": "# Paper\n\nConditional TV decreases for p = 5.\n",
        "output/tv_table.md": "| N | p | TV |\n|-|-|-|\n| 1000 | 5 | 51/500 |\n",
        "tables/extra/tv_long.md": "| N | p | residue | count |\n|-|-|-|-|\n",
    }.items():
        (project / rel).parent.mkdir(parents=True, exist_ok=True)
        (project / rel).write_text(text, encoding="utf-8")
    return project


def test_output_is_a_directory_name_like_outputs() -> None:
    assert "output/paper.md" in declared_paths(TASK)
    assert "output/tv_table.md" in declared_paths(TASK)
    # ...so a file a task declares there and never writes is reported missing.
    assert declared_paths("T009 Write `output/absent.md`.") == ["output/absent.md"]


def test_files_in_output_are_quoted_to_the_verifier(project: Path) -> None:
    evidence = task_verifier.gather_evidence(project, TASK)
    assert "Conditional TV decreases for p = 5." in evidence
    assert "| 1000 | 5 | 51/500 |" in evidence


def test_an_existing_file_in_a_directory_nobody_listed_is_evidence(project: Path) -> None:
    assert declared_existing_files(project, TASK) == ["tables/extra/tv_long.md"]
    assert "| N | p | residue | count |" in task_verifier.gather_evidence(project, TASK)


def test_a_path_that_is_only_text_is_not_reported_missing(project: Path) -> None:
    text = "T010 Follow `docs_old/guide.md` conventions and avoid `tmp/scratch.py`."
    assert declared_existing_files(project, text) == []
    assert "docs_old/guide.md" not in task_verifier.gather_evidence(project, text)


def test_a_named_path_cannot_leave_the_project(project: Path, tmp_path: Path) -> None:
    (tmp_path / "projects/secret.md").write_text("outside", encoding="utf-8")
    (project / "tables/link.md").symlink_to(tmp_path / "projects/secret.md")
    text = "T011 Read `../secret.md`, `tables/link.md` and `/etc/hosts.txt`."
    assert declared_existing_files(project, text) == []
