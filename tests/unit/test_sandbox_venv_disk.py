"""Per-project venvs must not accumulate until the runner's disk dies.

`cleanup_venv` existed but was NEVER CALLED anywhere. Each project venv is up to
1.2 GB (torch et al.), and ONE advance worker runs up to `--max-tasks 10` projects in
a single job — so the venvs piled up until the runner ran out of space. The
`Submission Intake` workflow failed with:

    ERROR: Could not install packages due to an OSError:
    [Errno 28] No space left on device

...and this was about to get much worse, because the execution-gate fixes push far
MORE projects into the stage that builds these venvs. Disk is now bounded to one
project's venv at a time: creating a venv evicts the OTHER projects' venvs first.
Nothing is lost — a CI job starts on a fresh runner anyway, and the SAME project's
venv is still reused across ticks within a job.
"""

from __future__ import annotations

from pathlib import Path

from llmxive import sandbox


def _fake_venv(projects: Path, pid: str) -> Path:
    v = projects / pid / "code" / ".venv"
    (v / "bin").mkdir(parents=True)
    (v / "bin" / "python").write_text("#!/bin/sh\n", encoding="utf-8")
    (v / "lib").mkdir()
    (v / "lib" / "big.so").write_text("x" * 1024, encoding="utf-8")
    return v


def test_creating_a_venv_evicts_other_projects_venvs(tmp_path: Path) -> None:
    projects = tmp_path / "projects"
    stale_a = _fake_venv(projects, "PROJ-552-knots")
    stale_b = _fake_venv(projects, "PROJ-261-dup")
    mine = projects / "PROJ-029-mine"
    (mine / "code").mkdir(parents=True)

    sandbox.evict_other_project_venvs(mine)

    assert not stale_a.exists(), "another project's 1.2GB venv was left on disk"
    assert not stale_b.exists()


def test_eviction_never_removes_the_current_projects_venv(tmp_path: Path) -> None:
    """The SAME project's venv must survive — it is reused across ticks."""
    projects = tmp_path / "projects"
    mine = projects / "PROJ-029-mine"
    my_venv = _fake_venv(projects, "PROJ-029-mine")
    _fake_venv(projects, "PROJ-552-knots")

    sandbox.evict_other_project_venvs(mine)

    assert my_venv.exists(), "evicted the venv we are about to use"
    assert (my_venv / "bin" / "python").exists()


def test_eviction_is_safe_when_there_is_nothing_to_evict(tmp_path: Path) -> None:
    mine = tmp_path / "projects" / "PROJ-001-only"
    (mine / "code").mkdir(parents=True)
    sandbox.evict_other_project_venvs(mine)  # must not raise
