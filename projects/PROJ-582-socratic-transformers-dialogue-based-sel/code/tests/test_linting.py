"""
Test suite to verify that the project adheres to the configured linting and formatting rules.
This ensures that T003 (Configure linting and formatting tools) is correctly set up.
"""
import subprocess
import sys
import os
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).parent.parent
CODE_DIR = PROJECT_ROOT

def test_ruff_check_passes():
    """Verify that ruff check passes with no errors."""
    result = subprocess.run(
        ["ruff", "check", "."],
        cwd=CODE_DIR,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, (
        f"Ruff check failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )

def test_black_check_passes():
    """Verify that black check passes with no formatting errors."""
    result = subprocess.run(
        ["black", "--check", "."],
        cwd=CODE_DIR,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, (
        f"Black check failed.\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
    )