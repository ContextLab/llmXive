"""
Test runner for the Statistical Bias in Pre-Print Server Publication Trends project.
Executes the full test suite using pytest and reports results.
"""
import subprocess
import sys
import os
from pathlib import Path

def run_pytest():
    """Run pytest on the tests/ directory with verbose output."""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        print(f"Error: Tests directory not found at {tests_dir}")
        return False

    # Construct pytest command
    # -v: verbose
    # --tb=short: short tracebacks
    # -x: stop on first failure (optional, can be removed to run all)
    # We run without -x to see all failures for T034's "fix any regressions" goal
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "--tb=short",
        "--strict-markers"
    ]

    print(f"Running: {' '.join(cmd)}")
    print("-" * 80)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            capture_output=False,  # Stream output for visibility
            text=True
        )
        
        print("-" * 80)
        if result.returncode == 0:
            print("SUCCESS: All tests passed.")
            return True
        else:
            print("FAILURE: Some tests failed. See output above.")
            return False
    except Exception as e:
        print(f"Error running pytest: {e}")
        return False

if __name__ == "__main__":
    success = run_pytest()
    sys.exit(0 if success else 1)