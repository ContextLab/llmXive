"""
Test runner for the Statistical Bias in Pre-Print Server Publication Trends project.
Executes the full test suite using pytest and reports results.

This script is invoked by task T034 to run all unit and integration tests.
"""
import sys
import subprocess
import os
from pathlib import Path

def run_pytest_suite():
    """
    Runs pytest on the entire tests/ directory with verbose output.
    Returns the exit code of the pytest process.
    """
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        print(f"Error: Tests directory not found at {tests_dir}")
        return 1

    # Construct pytest command
    # -v: verbose
    # -rA: show extra test summary info (all)
    # --tb=short: short tracebacks
    # --color=yes: force color output
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "-rA",
        "--tb=short",
        "--color=yes"
    ]

    print(f"Running: {' '.join(cmd)}")
    print("-" * 80)
    
    result = subprocess.run(cmd, cwd=project_root)
    
    print("-" * 80)
    if result.returncode == 0:
        print("SUCCESS: All tests passed.")
    else:
        print(f"FAILURE: pytest exited with code {result.returncode}")
        print("Please review the errors above and fix the failing tests.")
    
    return result.returncode

if __name__ == "__main__":
    exit_code = run_pytest_suite()
    sys.exit(exit_code)
