"""
T037: Run pytest suite to ensure all tests pass.

This script serves as the entry point to execute the full test suite for the
PROJ-066 project. It discovers tests in the `tests/` directory relative to the
project root and runs them using pytest.

Usage:
    python code/tests/run_all_tests.py
"""

import sys
import os
import subprocess
import argparse

# Ensure the project root is in the path so relative imports work
# We assume this script is at: projects/PROJ-.../code/tests/run_all_tests.py
# Project root is: projects/PROJ-.../
# The 'code' directory needs to be in sys.path for imports like 'from data.download import ...'
script_dir = os.path.dirname(os.path.abspath(__file__))
code_dir = os.path.dirname(script_dir)
project_root = os.path.dirname(code_dir)

if project_root not in sys.path:
    sys.path.insert(0, project_root)
if code_dir not in sys.path:
    sys.path.insert(0, code_dir)

def run_pytest():
    """
    Runs pytest with specific flags to ensure all tests pass.
    """
    print(f"Running test suite for project in: {project_root}")
    print(f"Python path includes: {sys.path}")

    # Construct the pytest command
    # -v: verbose
    # -x: stop on first failure
    # --tb=short: short traceback
    # tests/: directory containing tests
    cmd = [
        sys.executable, "-m", "pytest",
        "-v",
        "-x",
        "--tb=short",
        "tests/",
        "--rootdir", code_dir
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=code_dir,
            check=True,
            capture_output=False,
            text=True
        )
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"\n❌ Test suite failed with exit code {e.returncode}")
        return False
    except Exception as e:
        print(f"\n❌ Error running pytest: {e}")
        return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run the full pytest suite for PROJ-066.")
    parser.parse_args()

    success = run_pytest()
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please review the output above.")
        sys.exit(1)