"""
Task T046: Run pytest on all contract and unit tests to ensure full pipeline validity.

This script serves as the entry point to execute the full test suite.
It invokes pytest with appropriate flags to ensure all tests in the
tests/ directory (contract and unit subdirectories) are executed.

Usage:
    python tests/run_all_tests.py
"""
import sys
import subprocess
import os
from pathlib import Path

def main():
    """Run pytest on all tests in the project."""
    # Determine the project root (assuming this script is in tests/)
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        print(f"Error: Tests directory not found at {tests_dir}", file=sys.stderr)
        sys.exit(1)
    
    # Build pytest command
    # -v: verbose output
    # --tb=short: short traceback format
    # --strict-markers: treat unknown markers as errors
    # -x: stop on first failure (optional, remove for full run)
    # We remove -x to ensure we see all failures as per "full pipeline validity"
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "--tb=short",
        "--strict-markers",
        "--color=yes"
    ]
    
    print(f"Running test suite from: {tests_dir}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 60)
    
    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            env=os.environ,
            check=False  # We handle the return code explicitly
        )
        
        if result.returncode == 0:
            print("-" * 60)
            print("SUCCESS: All tests passed.")
            sys.exit(0)
        else:
            print("-" * 60)
            print(f"FAILURE: pytest exited with code {result.returncode}")
            print("Please review the errors above.")
            sys.exit(result.returncode)
            
    except KeyboardInterrupt:
        print("\nTest run interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"Error running pytest: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()