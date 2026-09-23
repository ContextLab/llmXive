"""
Unit tests for linting and formatting configuration validation.
Ensures ruff and black are correctly configured and can be invoked.
"""
import subprocess
import sys
import os
from pathlib import Path

import pytest


def get_project_root():
    """Get the project root directory (code/)."""
    return Path(__file__).parent.parent.parent / "code"


@pytest.mark.slow
def test_black_config_valid():
    """Verify that black can read its configuration without errors."""
    project_root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "--diff", "."],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    # If config is invalid, black exits with an error code and prints to stderr
    # We expect 0 (formatted) or 1 (not formatted but valid config).
    # 2+ indicates a configuration or system error.
    assert result.returncode < 2, f"Black configuration error: {result.stderr}"


@pytest.mark.slow
def test_ruff_config_valid():
    """Verify that ruff can read its configuration without errors."""
    project_root = get_project_root()
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "."],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    # Return code 0: no issues
    # Return code 1: issues found (valid config)
    # Return code 2: config error or internal error
    assert result.returncode < 2, f"Ruff configuration error: {result.stderr}"


def test_pyproject_toml_exists():
    """Ensure pyproject.toml exists in the code directory."""
    project_root = get_project_root()
    assert (project_root / "pyproject.toml").exists(), "pyproject.toml not found in code/"


def test_black_in_pyproject():
    """Verify black configuration exists in pyproject.toml."""
    project_root = get_project_root()
    content = (project_root / "pyproject.toml").read_text()
    assert "[tool.black]" in content, "Black configuration missing in pyproject.toml"


def test_ruff_in_pyproject():
    """Verify ruff configuration exists in pyproject.toml."""
    project_root = get_project_root()
    content = (project_root / "pyproject.toml").read_text()
    assert "[tool.ruff]" in content, "Ruff configuration missing in pyproject.toml"