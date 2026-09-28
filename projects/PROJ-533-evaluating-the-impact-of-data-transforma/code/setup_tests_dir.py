"""
Script to create and verify the 'tests/' directory for the project.
Implements Task T001d.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Creates the 'tests/' directory using mkdir -p logic and verifies its existence.
    Exits with code 0 on success, 1 on failure.
    """
    project_root = Path(__file__).resolve().parent.parent
    tests_dir = project_root / "tests"

    # Create directory if it doesn't exist (equivalent to mkdir -p)
    try:
        tests_dir.mkdir(parents=True, exist_ok=True)
        print(f"Successfully created or verified directory: {tests_dir}")
    except OSError as e:
        print(f"Error creating directory {tests_dir}: {e}", file=sys.stderr)
        sys.exit(1)

    # Verify existence (equivalent to test -d tests)
    if tests_dir.is_dir():
        print(f"Verification passed: {tests_dir} exists and is a directory.")
        sys.exit(0)
    else:
        print(f"Verification failed: {tests_dir} does not exist or is not a directory.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
