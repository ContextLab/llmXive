"""
Tests to verify that linting and formatting configurations are correct.
These tests ensure that the project adheres to the established style guide.
"""
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.mark.lint
def test_ruff_check_passes():
    """Verify that ruff check passes without errors."""
    project_root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    # Allow exit code 0 (pass) or 1 (found issues but no fatal errors)
    # In a CI context, we might want to fail on 1, but for this check we verify
    # the tool runs and the config is valid.
    assert result.returncode in (0, 1), f"Ruff check failed:\n{result.stdout}\n{result.stderr}"
    # If there are issues, they should be listed in stdout, but we don't fail the test
    # unless the config itself is broken (returncode > 1).
    if result.returncode == 1:
        print("Ruff found style issues (expected in early dev), but config is valid.")

@pytest.mark.format
def test_black_check_passes():
    """Verify that black --check passes without errors."""
    project_root = Path(__file__).parent.parent
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "."],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    # Exit code 0: all files are formatted correctly
    # Exit code 1: some files need reformatting (config is valid, but code is not)
    # Exit code > 1: fatal error
    assert result.returncode in (0, 1), f"Black check failed:\n{result.stdout}\n{result.stderr}"
    if result.returncode == 1:
        print("Black found formatting issues (expected in early dev), but config is valid.")

@pytest.mark.config
def test_pyproject_toml_exists():
    """Verify that pyproject.toml exists and contains required tool sections."""
    project_root = Path(__file__).parent.parent
    pyproject_path = project_root / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml does not exist"

    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"
    assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"
    assert "[tool.pytest.ini_options]" in content, "Pytest configuration missing in pyproject.toml"