"""
T046: Run the full test suite to verify all acceptance scenarios.

This script discovers and executes all tests in the `tests/` directory
using pytest. It is designed to be run as:
    python tests/run_all_tests.py

It ensures that all previously implemented test files (T010-T012, T018, T020-T021,
T027-T028, T035) are executed and reports the final status.
"""
import sys
import subprocess
import os
from pathlib import Path

def run_test_suite():
    """Run pytest on the tests directory with verbose output."""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"

    if not tests_dir.exists():
        print("ERROR: tests/ directory not found.", file=sys.stderr)
        sys.exit(1)

    # Ensure we are in the project root for imports to work correctly
    os.chdir(project_root)

    # Construct the pytest command
    # -v: verbose
    # --tb=short: short traceback format
    # -x: stop after first failure (optional, but good for CI)
    # We omit -x to ensure all tests run even if one fails, to get a full report
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "--tb=short",
        "--color=yes"
    ]

    print(f"Running test suite from: {project_root}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 80)

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            check=False,  # We handle the exit code manually
            capture_output=False,  # Stream output to console
            text=True
        )

        if result.returncode == 0:
            print("-" * 80)
            print("SUCCESS: All tests passed.")
            return True
        else:
            print("-" * 80)
            print("FAILURE: One or more tests failed.")
            return False

    except KeyboardInterrupt:
        print("\nTest suite interrupted by user.")
        sys.exit(130)
    except Exception as e:
        print(f"ERROR: Failed to run test suite: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    success = run_test_suite()
    sys.exit(0 if success else 1)