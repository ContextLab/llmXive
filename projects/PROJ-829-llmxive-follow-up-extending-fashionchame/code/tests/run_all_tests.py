import subprocess
import sys
import os
from pathlib import Path

def main():
    """
    Runs all unit and integration tests using pytest.
    Exits with the pytest return code (0 for success, non-zero for failure).
    """
    project_root = Path(__file__).resolve().parent.parent
    tests_dir = project_root / "tests"

    if not tests_dir.exists():
        print(f"Error: Tests directory not found at {tests_dir}", file=sys.stderr)
        sys.exit(1)

    # Construct pytest command
    # -v: verbose output
    # --tb=short: short traceback format
    # --strict-markers: ensure markers are registered
    # -x: stop after first failure
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "--tb=short",
        "--strict-markers",
        "-x"
    ]

    print(f"Running tests from {tests_dir}...")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 80)

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("-" * 80)
        print("SUCCESS: All tests passed.")
    else:
        print("-" * 80)
        print("FAILURE: One or more tests failed.")

    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
