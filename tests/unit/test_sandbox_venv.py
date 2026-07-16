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

import pytest

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


def test_ensure_venv_tolerates_a_bad_requirement_line(tmp_path: Path) -> None:
    """A single un-installable requirement (e.g. a local module or a namespace
    submodule wrongly auto-added — the PROJ-262 stall) must NOT crash
    ensure_venv or leave the venv unusable. The old batch-only
    `pip install -r` aborted the WHOLE set on one bad line, so even numpy never
    installed and every analysis script died ModuleNotFoundError. The resilient
    fallback installs per-package so good deps land; here we assert the bad line
    is tolerated and the venv stays functional (the 'good deps survive' invariant
    is verified end-to-end by the real analysis re-run in CI)."""
    proj = tmp_path / "projects" / "PROJ-BADREQ"
    (proj / "code").mkdir(parents=True)
    (proj / "code" / "requirements.txt").write_text(
        "llmxive-nonexistent-package-zzz999  # bogus, must be skipped\n",
        encoding="utf-8",
    )
    py = sandbox.ensure_venv(proj)  # must not raise
    assert py.exists()
    # The venv is still usable + its bundled pip is intact (the bad line didn't
    # corrupt or abort the environment).
    res = sandbox.run_in_venv(
        project_dir=proj,
        args=["-c", "import sys, pip; print('venv-ok')"],
        timeout_s=120,
    )
    assert res.ok, res.stderr
    assert "venv-ok" in res.stdout


@pytest.mark.slow
def test_ensure_venv_installs_abi_consistent_scipy_stack(tmp_path: Path) -> None:
    """Issue #1139 RC-C: an unpinned scientific stack alongside a bad line must
    land an ABI-CONSISTENT numpy/pandas set — the old per-package fallback could
    install numpy 2.x next to a pandas wheel built for numpy 1.x, breaking with
    `cannot import name '__version__' from numpy` / `pandas.compat.numpy` (the
    PROJ-262/300 ABI stall). Prune-and-rebatch reconciles the survivors in one
    resolver pass. Real install; verifies numpy and pandas import AND interoperate.
    """
    proj = tmp_path / "projects" / "PROJ-ABICONSISTENT"
    (proj / "code").mkdir(parents=True)
    (proj / "code" / "requirements.txt").write_text(
        "numpy\npandas\nllmxive-nonexistent-package-zzz999  # bogus, must be skipped\n",
        encoding="utf-8",
    )
    py = sandbox.ensure_venv(proj)  # must not raise despite the bad line
    assert py.exists()
    # numpy AND pandas import and INTEROPERATE — proves the ABI is consistent
    # (a numpy/pandas ABI skew raises on `import pandas` or on DataFrame creation).
    res = sandbox.run_in_venv(
        project_dir=proj,
        args=[
            "-c",
            "import numpy, pandas; "
            "df = pandas.DataFrame(numpy.arange(6).reshape(2, 3)); "
            "print('abi-ok', df.to_numpy().sum())",
        ],
        timeout_s=600,
    )
    assert res.ok, res.stderr
    assert "abi-ok 15" in res.stdout
