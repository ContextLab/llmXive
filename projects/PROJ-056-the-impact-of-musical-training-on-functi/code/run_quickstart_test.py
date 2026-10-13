"""
Script to execute the quick‑start unit test and exit with the pytest status.
This satisfies the verification requirement that the test suite has been run
and passed as part of task T001.
"""

import subprocess
import sys
import pathlib

def main() -> int:
    # Ensure we are at the project root
    project_root = pathlib.Path(__file__).resolve().parents[2]
    # Run pytest on the specific test file
    result = subprocess.run(
        [sys.executable, "-m", "pytest", "-q", "tests/unit/test_quickstart.py"],
        cwd=project_root,
        capture_output=True,
        text=True,
    )
    # Print pytest output for logging / visibility
    print(result.stdout)
    print(result.stderr, file=sys.stderr)
    return result.returncode

if __name__ == "__main__":
    sys.exit(main())
