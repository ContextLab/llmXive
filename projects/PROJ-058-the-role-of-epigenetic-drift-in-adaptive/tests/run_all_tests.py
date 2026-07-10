"""
T043: Run pytest and verify all tests pass.
This script executes pytest against the project's test suite.
It ensures all unit and contract tests pass before considering the project ready.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    project_root = Path(__file__).parent.parent
    os.chdir(project_root)

    # Ensure pytest is available (it should be in requirements.txt from T002)
    # Construct the pytest command
    # -v: verbose
    # --tb=short: short tracebacks
    # tests/: run everything in the tests directory
    cmd = [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"]

    print(f"Running: {' '.join(cmd)}")
    print("-" * 50)

    result = subprocess.run(cmd)

    if result.returncode == 0:
        print("-" * 50)
        print("SUCCESS: All tests passed.")
        return 0
    else:
        print("-" * 50)
        print("FAILURE: Some tests failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())