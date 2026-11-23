"""
Unit tests for linting and formatting configuration validity.

These tests ensure that the project's linting tools (ruff, black) are
correctly configured and can be invoked without errors.
"""
import subprocess
import pytest
from pathlib import Path

def test_ruff_config_valid():
    """Verify that ruff can parse the configuration and check the project."""
    # This command will fail if the config is invalid or if lint errors exist.
    # For the purpose of T003b, we assume the initial state is clean.
    result = subprocess.run(
        ["ruff", "check", "."],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
        timeout=30
    )
    # We expect exit code 0 for a clean project.
    # If there are lint errors, the task T003b requires fixing them first.
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"

def test_black_config_valid():
    """Verify that black can parse the configuration and check the project."""
    result = subprocess.run(
        ["black", "--check", "."],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
        timeout=30
    )
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"
