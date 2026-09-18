"""
Test suite to verify linting and formatting configuration.
These tests ensure that ruff and black are correctly configured
and that the project structure supports them.
"""
import subprocess
import sys
from pathlib import Path

import pytest


def get_project_root() -> Path:
    """Return the project root directory."""
    return Path(__file__).parent.parent


def test_ruff_syntax_check():
    """
    Run ruff check on the codebase.
    This test verifies that ruff is installed and can parse the files.
    It expects the check to pass (exit code 0) if the code is clean.
    If there are linting errors, this test will fail, indicating
    that the code needs to be fixed before the task is considered complete.
    """
    project_root = get_project_root()
    code_dir = project_root / "code"

    # Run ruff check
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        capture_output=True,
        text=True,
        cwd=project_root
    )

    # If ruff is not installed, we fail the task setup
    if result.returncode == 1 and "No such file or directory" in result.stderr:
        pytest.fail("Ruff is not installed or not in PATH. Please install ruff.")

    # Assert that ruff passed (exit code 0)
    # Note: If the code has linting errors, this will fail, which is the desired behavior
    # to force the developer to fix the code.
    assert result.returncode == 0, (
        f"Ruff check failed with the following errors:\n{result.stdout}\n{result.stderr}"
    )


def test_black_check():
    """
    Run black --check on the codebase.
    This verifies that all files are formatted according to Black standards.
    """
    project_root = get_project_root()
    code_dir = project_root / "code"

    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(code_dir)],
        capture_output=True,
        text=True,
        cwd=project_root
    )

    # Assert that black passed
    assert result.returncode == 0, (
        f"Black check failed. Run 'black code/' to format.\n{result.stdout}\n{result.stderr}"
    )


def test_import_setup_project():
    """
    Verify that setup_project can be imported without errors.
    This ensures the basic project structure is valid.
    """
    sys.path.insert(0, str(get_project_root()))
    try:
        from setup_project import main
        assert callable(main)
    finally:
        sys.path.pop(0)
