"""
Test suite to verify that linting (ruff) and formatting (black) configurations
are correctly set up and enforceable.

These tests ensure that the project adheres to the defined code style standards.
"""
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def project_root():
    """Return the project root directory."""
    return Path(__file__).parent.parent


def test_ruff_check_passes(project_root):
    """Verify that ruff check passes without errors on the codebase."""
    result = subprocess.run(
        ["ruff", "check", "."],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Ruff check failed:\n{result.stdout}\n{result.stderr}"
    )


def test_black_check_passes(project_root):
    """Verify that black --check passes without differences."""
    result = subprocess.run(
        ["black", "--check", "."],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Black check failed:\n{result.stdout}\n{result.stderr}"
    )


def test_ruff_config_exists(project_root):
    """Verify that ruff configuration file exists."""
    ruff_config = project_root / "pyproject.toml"
    assert ruff_config.exists(), "ruff configuration (pyproject.toml) not found"
    content = ruff_config.read_text()
    assert "[tool.ruff" in content, "ruff configuration section missing in pyproject.toml"


def test_black_config_exists(project_root):
    """Verify that black configuration exists."""
    black_config = project_root / "pyproject.toml"
    assert black_config.exists(), "black configuration (pyproject.toml) not found"
    content = black_config.read_text()
    assert "[tool.black" in content, "black configuration section missing in pyproject.toml"