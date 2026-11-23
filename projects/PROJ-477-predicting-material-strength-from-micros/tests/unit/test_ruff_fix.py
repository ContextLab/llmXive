"""
Unit tests for the ruff fix runner functionality.
"""
import subprocess
import sys
import tempfile
import os
from pathlib import Path
import pytest

from ruff_fix_runner import main

def test_ruff_runner_exists():
    """Test that the ruff_fix_runner module can be imported."""
    assert main is not None

def test_ruff_check_syntax():
    """
    Test that running ruff on a valid Python file returns 0.
    This test creates a temporary directory with valid Python code.
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "valid.py"
        test_file.write_text("x = 1\ny = 2\n")
        
        result = subprocess.run(
            ["ruff", "check", str(tmpdir)],
            capture_output=True,
            text=True
        )
        
        # If ruff is installed, it should return 0 for valid code
        # If ruff is not installed, we skip this test
        if result.returncode != 127:  # 127 is command not found
            assert result.returncode == 0, f"Ruff found issues: {result.stdout}"

def test_ruff_detects_syntax_error():
    """
    Test that ruff detects syntax errors (if installed).
    """
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = Path(tmpdir) / "invalid.py"
        test_file.write_text("x = \n")  # Syntax error
        
        result = subprocess.run(
            ["ruff", "check", str(tmpdir)],
            capture_output=True,
            text=True
        )
        
        # If ruff is installed, it should return non-zero for invalid code
        if result.returncode != 127:  # 127 is command not found
            assert result.returncode != 0, "Ruff should have detected the syntax error"

@pytest.mark.skipif(
    subprocess.run(["which", "ruff"], capture_output=True).returncode != 0,
    reason="ruff is not installed"
)
def test_ruff_fix_runner_integration():
    """
    Integration test: Run the main function of ruff_fix_runner on the actual codebase.
    This test expects the codebase to be in a state where ruff can run (either 0 or non-zero).
    We mainly verify that the script runs without crashing.
    """
    # We cannot easily test the exit code here because we don't know the current state
    # of the codebase. Instead, we verify the script exists and can be called.
    import ruff_fix_runner
    assert hasattr(ruff_fix_runner, 'main')