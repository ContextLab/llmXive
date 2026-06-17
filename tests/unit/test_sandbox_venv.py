"""Regression: the execution sandbox must run the PROJECT venv's python.

`run_in_venv` once did ``ensure_venv(project_dir).resolve()`` — but a venv's
``bin/python`` is a SYMLINK to the base interpreter, so ``.resolve()`` followed
it and executed the SYSTEM python instead of the venv. That silently ran every
project's analysis against the base interpreter's packages (niche venv-only
deps like ``database_knotinfo`` → ModuleNotFoundError; common globally-installed
deps masked the bug). These tests pin that the venv — and its site-packages —
are actually used.
"""

from __future__ import annotations

from pathlib import Path

from llmxive import sandbox


def _site_packages(venv: Path) -> Path:
    cands = list((venv / "lib").glob("python*/site-packages"))
    assert cands, f"no site-packages under {venv}"
    return cands[0]


def test_run_in_venv_uses_the_project_venv_python(tmp_path: Path) -> None:
    proj = tmp_path / "projects" / "PROJ-X"
    (proj / "code").mkdir(parents=True)
    sandbox.ensure_venv(proj)
    res = sandbox.run_in_venv(
        project_dir=proj,
        args=["-c", "import sys; print(sys.executable)"],
        timeout_s=120,
    )
    assert res.ok, res.stderr
    exe = res.stdout.strip()
    # The reported interpreter must live INSIDE the project's code/.venv — not
    # the base interpreter the venv symlink points at.
    assert str((proj / "code" / ".venv").resolve()) in exe or "code/.venv" in exe, exe


def test_run_in_venv_sees_venv_only_site_packages(tmp_path: Path) -> None:
    """A module present ONLY in the venv's site-packages must be importable —
    proving the venv interpreter (with its site-packages) is what runs, not the
    base python (which can't see it)."""
    proj = tmp_path / "projects" / "PROJ-Y"
    (proj / "code").mkdir(parents=True)
    py = sandbox.ensure_venv(proj)
    venv = py.parent.parent  # ensure_venv returns .../bin/python; venv dir is two up
    (_site_packages(venv) / "_venv_only_probe.py").write_text(
        "MARKER = 'in-the-venv'\n", encoding="utf-8"
    )
    res = sandbox.run_in_venv(
        project_dir=proj,
        args=["-c", "import _venv_only_probe; print(_venv_only_probe.MARKER)"],
        timeout_s=120,
    )
    assert res.ok, res.stderr
    assert "in-the-venv" in res.stdout
