"""
T045: Run all unit tests for User Story 1.

This script executes the unit tests defined in tests/test_preprocess.py.
It serves as the pipeline gate: if tests fail, the pipeline halts.
"""
import sys
import subprocess
from pathlib import Path

def main():
    """Run pytest on the tests directory and exit with appropriate code."""
    project_root = Path(__file__).parent.parent
    tests_dir = project_root / "tests"
    
    if not tests_dir.exists():
        print(f"ERROR: Tests directory not found at {tests_dir}")
        sys.exit(1)

    print(f"Running tests in {tests_dir}...")
    
    # Run pytest with verbose output and fail-fast behavior
    # -x: Stop running tests after the first failure
    # -v: Verbose output
    # --tb=short: Short traceback format
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-x",
        "-v",
        "--tb=short"
    ]

    try:
        result = subprocess.run(
            cmd,
            cwd=project_root,
            check=False,  # We handle the exit code manually
            capture_output=False,
            text=False
        )

        if result.returncode == 0:
            print("\n" + "="*50)
            print("SUCCESS: All unit tests passed.")
            print("="*50 + "\n")
            sys.exit(0)
        else:
            print("\n" + "="*50)
            print("FAILURE: One or more unit tests failed.")
            print("Pipeline halted as per T045 requirements.")
            print("="*50 + "\n")
            sys.exit(1)
            
    except FileNotFoundError:
        print("ERROR: pytest not found. Ensure dependencies are installed.")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR: Failed to run tests: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
