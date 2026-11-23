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
    # The reported interpreter must live INSIDE the project's venv — not the
    # base interpreter the venv symlink points at.
    assert Path(exe).is_relative_to(sandbox.venv_dir(proj)), exe


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


@pytest.mark.parametrize("through_symlink", [False, True])
def test_run_in_venv_rejects_external_working_directory_before_execution(tmp_path, through_symlink):
    proj = tmp_path / "projects" / "PROJ-CWD"
    proj.mkdir(parents=True)
    cwd = tmp_path
    if through_symlink:
        cwd = proj / "escape"
        cwd.symlink_to(tmp_path, target_is_directory=True)
    result = sandbox.run_in_venv(
        project_dir=proj, cwd=cwd,
        args=["-c", "from pathlib import Path; Path('leak.csv').write_text('data')"],
    )
    assert not result.ok
    assert "working directory escapes" in result.stderr
    assert not (tmp_path / "leak.csv").exists()
    assert not sandbox.venv_dir(proj).exists()
    assert not (proj / "code" / ".venv").exists()


# --- the venv is the platform's, and lives outside the project ----------------


def test_the_venv_is_never_inside_the_project(tmp_path: Path) -> None:
    for proj in (tmp_path / "projects" / "PROJ-X", tmp_path / "bare-workspace"):
        (proj / "code").mkdir(parents=True)
        venv = sandbox.venv_dir(proj)
        assert venv.is_absolute()
        assert not venv.is_relative_to(proj.resolve()) and not venv.is_relative_to(proj)
    repo_style = sandbox.venv_dir(tmp_path / "projects" / "PROJ-X")
    assert repo_style == tmp_path / sandbox.VENV_ROOT_NAME / "PROJ-X"
    # Two bare workspaces that share a parent do not share a root, so creating
    # one's venv can never evict the other's.
    assert sandbox.venv_root(tmp_path / "a") != sandbox.venv_root(tmp_path / "b")


def test_a_project_that_deletes_code_venv_cannot_break_its_own_run(tmp_path: Path) -> None:
    """The PROJ-9999 canary failure, byte for byte in its mechanism.

    The generated ``conftest.py`` ran ``shutil.rmtree("code/.venv")`` in
    ``pytest_configure`` to hide site-packages from the project's own import
    scan. When the venv lived there, pytest deleted the interpreter it was
    running from and every test module died on its first third-party import.
    """
    proj = tmp_path / "projects" / "PROJ-X"
    (proj / "code").mkdir(parents=True)
    (proj / "tests").mkdir()
    py = sandbox.ensure_venv(proj)
    site = next(sandbox.venv_dir(proj).glob("lib/python*/site-packages"))
    (site / "only_in_the_venv.py").write_text("VALUE = 41\n", encoding="utf-8")
    (proj / "conftest.py").write_text(
        "import shutil\nfrom pathlib import Path\n\n"
        "def pytest_configure(config):\n"
        "    venv = Path(__file__).parent / 'code' / '.venv'\n"
        "    if venv.is_dir():\n"
        "        shutil.rmtree(venv)\n",
        encoding="utf-8",
    )
    (proj / "tests" / "test_dep.py").write_text(
        "def test_dep():\n    import only_in_the_venv\n    assert only_in_the_venv.VALUE == 41\n",
        encoding="utf-8",
    )
    import subprocess

    subprocess.run([str(py), "-m", "pip", "install", "-q", "pytest"], check=True, capture_output=True)
    for _ in range(2):  # the second run is the one that used to find no venv
        res = sandbox.run_in_venv(project_dir=proj, args=["-m", "pytest", "-q", "tests/"], timeout_s=300)
        assert res.ok, res.stdout + res.stderr
    assert py.exists()


def test_a_venv_left_inside_the_project_is_removed(tmp_path: Path) -> None:
    proj = tmp_path / "projects" / "PROJ-X"
    legacy = proj / "code" / ".venv"
    (legacy / "bin").mkdir(parents=True)
    (legacy / "bin" / "python").write_text("#!/bin/sh\n", encoding="utf-8")
    py = sandbox.ensure_venv(proj)
    assert not legacy.exists()
    assert py.exists() and py.is_relative_to(sandbox.venv_dir(proj))
