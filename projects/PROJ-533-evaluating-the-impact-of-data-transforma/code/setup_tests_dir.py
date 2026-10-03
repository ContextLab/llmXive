import os
import sys
from pathlib import Path

def main():
    """
    Creates the 'tests' directory at the project root and verifies its existence.
    This script implements task T001d: Create tests/ directory.
    """
    project_root = Path(__file__).resolve().parent.parent
    tests_dir = project_root / "tests"

    # Create the directory if it doesn't exist
    os.makedirs(tests_dir, exist_ok=True)

    # Verify existence (equivalent to 'test -d tests')
    if tests_dir.is_dir():
        print(f"Successfully created and verified: {tests_dir}")
        return 0
    else:
        print(f"ERROR: Failed to create or verify directory: {tests_dir}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())
