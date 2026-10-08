"""Regression: run_pytest must resolve the venv python absolutely.

`run_pytest` used the venv python path exactly as ``ensure_venv`` returned
it. When ``project_dir`` is RELATIVE (e.g. ``Path("projects/PROJ-x")``),
that path is relative too — and because run_pytest spawns the subprocess
with ``cwd=project_dir/code``, the relative executable no longer resolves
from the new cwd and subprocess raises FileNotFoundError. The fix anchors
the venv python with ``os.path.abspath`` (symlink-preserving, same as
run_in_venv) while keeping the pytest target path relative to the code
directory.
"""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from llmxive import sandbox


def test_run_pytest_with_relative_project_dir(tmp_path: Path) -> None:
    """A RELATIVE project_dir must not break venv executable resolution.

    Uses a real venv (created with --system-site-packages so the already
    installed pytest is visible — no downloads) and a real subprocess run
    of pytest. On the buggy code this raises FileNotFoundError because the
    relative 'projects/PROJ-relative/code/.venv/bin/python' is looked up
    under the changed cwd (projects/PROJ-relative/code).
    """
    # Build the project tree under tmp_path, then chdir there so the
    # project_dir we pass is genuinely RELATIVE.
    proj = tmp_path / "projects" / "PROJ-relative"
    code = proj / "code"
    (code / "tests").mkdir(parents=True)
    venv = code / ".venv"
    subprocess.run(
        [sys.executable, "-m", "venv", "--system-site-packages", str(venv)],
        check=True,
        capture_output=True,
    )
    (code / "tests" / "test_ok.py").write_text(
        "def test_ok():\n    assert True\n", encoding="utf-8"
    )

    old_cwd = Path.cwd()
    try:
        import os

        os.chdir(tmp_path)
        rel_proj = Path("projects") / "PROJ-relative"
        assert not rel_proj.is_absolute()
        res = sandbox.run_pytest(
            project_dir=rel_proj, test_path="tests/", timeout_s=300
        )
    finally:
        os.chdir(old_cwd)

    assert res.ok, f"stdout={res.stdout!r}\nstderr={res.stderr!r}"
    # The pytest target path stayed relative to the project code dir.
    assert "1 passed" in res.stdout


def test_run_pytest_reports_failing_tests_with_relative_project_dir(
    tmp_path: Path,
) -> None:
    """Same setup, but with a failing test: proves the venv python actually
    ran pytest (a FileNotFoundError would surface as an unhandled exception
    on the buggy code, not as a pytest failure report)."""
    proj = tmp_path / "projects" / "PROJ-relative"
    code = proj / "code"
    (code / "tests").mkdir(parents=True)
    venv = code / ".venv"
    subprocess.run(
        [sys.executable, "-m", "venv", "--system-site-packages", str(venv)],
        check=True,
        capture_output=True,
    )
    (code / "tests" / "test_fail.py").write_text(
        "def test_fail():\n    assert False, 'intentional'\n", encoding="utf-8"
    )

    old_cwd = Path.cwd()
    try:
        import os

        os.chdir(tmp_path)
        rel_proj = Path("projects") / "PROJ-relative"
        res = sandbox.run_pytest(
            project_dir=rel_proj, test_path="tests/", timeout_s=300
        )
    finally:
        os.chdir(old_cwd)

    assert not res.ok
    assert "1 failed" in res.stdout
    assert "intentional" in res.stdout
