"""
Script to run the full test suite for the llmXive project.
Executes pytest with verbose output and coverage reporting.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_tests():
    """Run pytest with coverage and verbose flags."""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        print(f"Error: Tests directory not found at {tests_dir}")
        sys.exit(1)

    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "--cov=code",
        "--cov-report=term-missing",
        "--cov-report=xml:results/coverage.xml",
        "--cov-report=html:results/htmlcov",
        str(tests_dir)
    ]

    print(f"Running tests from: {tests_dir}")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            check=True,
            capture_output=False,
            text=True
        )
        print("\n--- Test Execution Successful ---")
        return 0
    except subprocess.CalledProcessError as e:
        print(f"\n--- Test Execution Failed with exit code {e.returncode} ---")
        sys.exit(e.returncode)

if __name__ == "__main__":
    sys.exit(run_tests())
