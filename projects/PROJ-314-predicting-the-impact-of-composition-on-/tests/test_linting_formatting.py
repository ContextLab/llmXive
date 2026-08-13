"""
Tests to verify that linting and formatting configurations are valid
and that the codebase adheres to them.
"""
import subprocess
import sys
from pathlib import Path

import pytest


def test_ruff_check_passes():
    """Ensure ruff finds no errors in the codebase."""
    code_dir = Path(__file__).parent.parent / "code"
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        capture_output=True,
        text=True,
    )
    # We expect exit code 0 (success). If 1, it means lint errors found.
    # If 2, it means config error.
    assert result.returncode == 0, (
        f"Ruff check failed:\n{result.stdout}\n{result.stderr}"
    )


def test_black_check_passes():
    """Ensure black finds no formatting issues in the codebase."""
    code_dir = Path(__file__).parent.parent / "code"
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(code_dir)],
        capture_output=True,
        text=True,
    )
    assert result.returncode == 0, (
        f"Black check failed:\n{result.stdout}\n{result.stderr}"
    )