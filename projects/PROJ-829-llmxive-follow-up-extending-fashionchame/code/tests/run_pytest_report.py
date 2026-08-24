"""
Script to run pytest and generate a summary report to stdout.
This fulfills T040 by executing the test suite and ensuring results are visible.
"""
import subprocess
import sys
import os
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    tests_dir = project_root / "tests"
    
    # Ensure we are in the project root for imports to work correctly if needed
    os.chdir(project_root)

    if not tests_dir.exists():
        print(f"Error: Tests directory not found at {tests_dir}", file=sys.stderr)
        return 1

    # Run pytest with verbose output to stdout
    # We use -v to see details, --tb=short for clean tracebacks
    cmd = [
        sys.executable, "-m", "pytest",
        str(tests_dir),
        "-v",
        "--tb=short",
        "--maxfail=1",  # Stop on first error to save time if broken
        "--import-mode=importlib"
    ]

    print(f"Executing: {' '.join(cmd)}")
    print("=" * 80)

    try:
        # Run directly in the current process to capture output correctly
        # or use subprocess.run if isolation is needed. 
        # Using subprocess.run with capture_output=False to stream to console
        result = subprocess.run(cmd)
        
        if result.returncode == 0:
            print("=" * 80)
            print("T040 VERIFICATION: All tests passed successfully.")
            return 0
        else:
            print("=" * 80)
            print("T040 VERIFICATION: Tests failed.")
            return result.returncode
    except FileNotFoundError:
        print("Error: pytest not found. Please install it via `pip install pytest`.")
        return 1
    except Exception as e:
        print(f"Error running tests: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())