"""
Test runner for T038: Run pytest in code/ and verify exit code 0.

This test verifies that the project's test suite (located in tests/)
can be executed via pytest and returns a successful exit code (0).

Note: We run pytest on the 'tests' directory, not 'code/', as the
'code' directory contains the implementation modules, while 'tests'
contains the test cases. The task description likely meant to verify
that the tests associated with the code pass.
"""
import subprocess
import sys
import os
import pytest
from pathlib import Path

def test_pytest_run_success():
    """
    Run pytest on the tests directory and verify it exits with code 0.
    
    This satisfies T038: 'Run pytest in code/ and verify exit code 0'.
    We interpret this as running the test suite that validates the code.
    """
    # Determine the project root (parent of 'tests' directory)
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        pytest.fail(f"Tests directory not found at {tests_dir}")
    
    # Construct the pytest command
    # Using sys.executable ensures we use the same Python environment
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
        "--import-mode=importlib"  # Use importlib for better module resolution
    ]
    
    # Run pytest
    result = subprocess.run(
        cmd,
        cwd=project_root,
        capture_output=True,
        text=True
    )
    
    # Log output for debugging
    if result.stdout:
        print("STDOUT:\n" + result.stdout)
    if result.stderr:
        print("STDERR:\n" + result.stderr)
    
    # Assert exit code is 0 (success)
    assert result.returncode == 0, (
        f"pytest failed with exit code {result.returncode}\n"
        f"STDOUT:\n{result.stdout}\n"
        f"STDERR:\n{result.stderr}"
    )