"""
Unit test for the CI skeleton‑check script.

The test creates a temporary project layout, deliberately removes one of the
required directories, and asserts that the script exits with a non‑zero
status code.  It also verifies that when all directories are present the
script exits with status 0.
"""
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def temp_project(tmp_path):
    """
    Create a minimal repository skeleton in a temporary directory.
    Required top‑level directories (as defined elsewhere in the project) are:
    src/, tests/, data/, results/, docs/, contracts/
    """
    required = ["src", "tests", "data", "results", "docs", "contracts"]
    for d in required:
        (tmp_path / d).mkdir()
    return tmp_path


def run_check_script(project_root: Path) -> subprocess.CompletedProcess:
    """
    Execute the ``check_skeleton_ci.py`` script with the working directory set
    to ``project_root``.  The script is located at ``code/ci/check_skeleton_ci.py``.
    """
    script_path = Path(__file__).parents[2] / "code" / "ci" / "check_skeleton_ci.py"
    # Ensure the script is executable; if not, invoke via the interpreter.
    return subprocess.run(
        [sys.executable, str(script_path)],
        cwd=project_root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True,
    )


def test_check_skeleton_all_present(temp_project):
    """When all required directories exist the script should exit with 0."""
    result = run_check_script(temp_project)
    assert result.returncode == 0, f"Unexpected failure: {result.stderr}"


def test_check_skeleton_missing_directory(temp_project):
    """If a required directory is missing the script must exit with non‑zero."""
    # Remove one required directory (e.g., 'docs')
    (temp_project / "docs").rmdir()
    result = run_check_script(temp_project)
    assert result.returncode != 0
    assert "Missing required repository skeleton directories" in result.stderr