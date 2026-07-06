"""
Test suite for Task T006: Linting and Formatting Configuration.

This test verifies that the project is configured with ruff and black,
and that the existing codebase passes the configured linting rules.
"""
import os
import subprocess
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent.parent


def test_ruff_config_exists():
    """Verify .ruff.toml configuration file exists."""
    config_path = PROJECT_ROOT / ".ruff.toml"
    assert config_path.exists(), f"Ruff config missing at {config_path}"


def test_black_config_exists():
    """Verify black configuration exists in pyproject.toml."""
    pyproject_path = PROJECT_ROOT / "pyproject.toml"
    assert pyproject_path.exists(), "pyproject.toml missing"
    content = pyproject_path.read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"


def test_ruff_lint_passes():
    """Run ruff lint on the codebase and ensure it passes."""
    ruff_path = PROJECT_ROOT / ".ruff.toml"
    # Run ruff check on the src and tests directories
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "--config", str(ruff_path), "src", "tests", "setup_project.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    # We expect exit code 0 for success. If there are linting errors, the task is incomplete.
    # Note: We ignore E501 (line length) as black handles that, but ruff might still complain if not configured to ignore.
    # The .ruff.toml explicitly ignores E501.
    assert result.returncode == 0, (
        f"Ruff linting failed:\n{result.stdout}\n{result.stderr}"
    )


def test_black_format_check():
    """Run black --check to ensure code is formatted correctly."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--config", str(PROJECT_ROOT / "pyproject.toml"), "src", "tests", "setup_project.py"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Black formatting check failed. Run 'black src tests setup_project.py' to fix.\n{result.stdout}\n{result.stderr}"
    )