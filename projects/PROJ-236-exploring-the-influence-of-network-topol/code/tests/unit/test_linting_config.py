"""
Unit tests to verify that linting and formatting configurations are valid
and that the codebase passes ruff and black checks.
"""
import subprocess
import sys
from pathlib import Path

import pytest


@pytest.fixture
def code_dir():
    """Return the path to the code directory."""
    return Path(__file__).parent.parent.parent / "code"


def test_ruff_check_passes(code_dir):
    """
    Verify that `ruff check` (or `ruff --quiet`) passes with no errors.
    This ensures the codebase adheres to the configured linting rules.
    """
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        capture_output=True,
        text=True,
        cwd=code_dir.parent,
    )
    assert result.returncode == 0, (
        f"Ruff check failed:\n{result.stdout}\n{result.stderr}"
    )


def test_black_check_passes(code_dir):
    """
    Verify that `black --check` passes with no formatting errors.
    This ensures the codebase adheres to the configured formatting rules.
    """
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(code_dir)],
        capture_output=True,
        text=True,
        cwd=code_dir.parent,
    )
    assert result.returncode == 0, (
        f"Black check failed:\n{result.stdout}\n{result.stderr}"
    )