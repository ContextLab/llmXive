"""
Test suite to verify linting and formatting configuration.
These tests ensure that the project adheres to the configured standards.
"""
import subprocess
import sys
from pathlib import Path

def test_black_formatting():
    """Verify that code passes Black formatting."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "code/", "tests/"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Black check failed:\n{result.stdout}\n{result.stderr}"

def test_ruff_linting():
    """Verify that code passes Ruff linting."""
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "code/", "tests/"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Ruff check failed:\n{result.stdout}\n{result.stderr}"