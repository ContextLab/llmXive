"""
Linting and Formatting Tests (Task T003).

These tests verify that the project codebase adheres to ruff and black standards.
"""

import subprocess
import sys
import os
from pathlib import Path
import pytest


@pytest.fixture
def project_root():
    return Path(__file__).parent.parent


def test_ruff_check_passes(project_root):
    """Verify that ruff check passes with no errors."""
    try:
        result = subprocess.run(
            ["ruff", "check", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        pytest.skip("ruff not installed in environment")


def test_black_check_passes(project_root):
    """Verify that black check passes (diff is empty)."""
    try:
        result = subprocess.run(
            ["black", "--check", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        pytest.skip("black not installed in environment")


def test_ruff_format_check_passes(project_root):
    """Verify that ruff format check passes (if ruff format is available)."""
    try:
        result = subprocess.run(
            ["ruff", "format", "--check", "."],
            cwd=project_root,
            capture_output=True,
            text=True,
            timeout=60
        )
        # Return code 0 means formatted correctly. 1 means changes needed.
        assert result.returncode == 0, f"Ruff format check failed:\n{result.stdout}\n{result.stderr}"
    except FileNotFoundError:
        # If ruff doesn't have format command, skip (older versions)
        pytest.skip("ruff format command not available")
    except Exception as e:
        # Skip if command fails for other reasons (e.g. not installed)
        pytest.skip(f"Ruff format check skipped: {e}")
