import subprocess
import sys
import os
from pathlib import Path

def test_ruff_check_runs():
    """Verify that ruff can be invoked and checks pass (or report issues)."""
    # Run ruff check on the code directory
    result = subprocess.run(
        [sys.executable, "-m", "ruff", "check", "code/"],
        capture_output=True,
        text=True
    )
    # We expect it to run without crashing. 
    # It may find linting errors in existing code, which is fine for this setup task.
    assert result.returncode in [0, 1], f"Ruff check failed to run: {result.stderr}"

def test_black_check_runs():
    """Verify that black can be invoked."""
    result = subprocess.run(
        [sys.executable, "-m", "black", "--check", "code/"],
        capture_output=True,
        text=True
    )
    # Returns 0 if all good, 1 if formatting needed. Both are valid execution states.
    assert result.returncode in [0, 1], f"Black check failed to run: {result.stderr}"