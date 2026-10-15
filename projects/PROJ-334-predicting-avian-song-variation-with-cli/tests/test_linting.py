"""
Test that the project's linting (ruff) and formatting (black) configurations
are valid and that the tools run without errors.
"""

import subprocess
import sys

def test_ruff_check():
    """ruff should exit with code 0 for the repository."""
    result = subprocess.run(
        ["ruff", "check", "."],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert result.returncode == 0, f"ruff failed: {result.stdout}"

def test_black_check():
    """black should exit with code 0 in check mode."""
    result = subprocess.run(
        ["black", "--check", "."],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )
    assert result.returncode == 0, f"black failed: {result.stdout}"
