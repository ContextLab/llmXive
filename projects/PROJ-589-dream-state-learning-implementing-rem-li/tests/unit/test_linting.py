"""
Unit tests for linting and formatting configuration.

These tests verify that the project's linting configuration (ruff)
and formatting configuration (black) are correctly set up and
that the codebase adheres to these standards.
"""

import subprocess
import sys
from pathlib import Path


def test_ruff_check_passes():
    """Verify that ruff check passes without errors."""
    project_root = Path(__file__).resolve().parent.parent.parent
    code_dir = project_root / "code"
    
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", str(code_dir)],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0, (
        f"Ruff check failed:\n{result.stdout}\n{result.stderr}"
    )


def test_black_check_passes():
    """Verify that black check passes without changes needed."""
    project_root = Path(__file__).resolve().parent.parent.parent
    code_dir = project_root / "code"
    
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", str(code_dir)],
        capture_output=True,
        text=True,
    )
    
    assert result.returncode == 0, (
        f"Black check failed:\n{result.stdout}\n{result.stderr}"
    )