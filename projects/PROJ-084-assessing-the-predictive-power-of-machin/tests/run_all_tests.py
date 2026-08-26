"""
T039: Run full test suite to ensure all contract and unit tests pass.

This script orchestrates the execution of the entire test suite using pytest.
It serves as the entry point for verifying the project's implementation
against its specifications and contracts.

Usage:
    python code/run_all_tests.py
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    """Run the full pytest suite."""
    # Ensure we are in the project root
    project_root = Path(__file__).resolve().parent.parent
    os.chdir(project_root)
    
    # Construct the pytest command
    # -v: verbose output
    # -x: stop on first failure
    # --tb=short: concise traceback
    # tests/: run all tests in the tests directory
    cmd = [
        sys.executable, "-m", "pytest", 
        "tests/", 
        "-v", 
        "-x", 
        "--tb=short",
        "--color=yes"
    ]
    
    print(f"Running test suite from: {project_root}")
    print(f"Command: {' '.join(cmd)}")
    print("-" * 50)
    
    try:
        result = subprocess.run(
            cmd,
            check=True,
            stdout=sys.stdout,
            stderr=sys.stderr,
            text=True
        )
        print("-" * 50)
        print("✅ All tests passed successfully!")
        return 0
    except subprocess.CalledProcessError as e:
        print("-" * 50)
        print("❌ Test suite failed. See output above for details.")
        return e.returncode
    except FileNotFoundError:
        print("❌ pytest not found. Please ensure it is installed in the environment.")
        return 1

if __name__ == "__main__":
    sys.exit(main())