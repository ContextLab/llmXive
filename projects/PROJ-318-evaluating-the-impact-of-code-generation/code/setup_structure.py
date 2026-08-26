import os
import sys
from pathlib import Path

def main():
    """
    Creates the required project directory structure for PROJ-318.
    This script ensures all necessary folders for code, data, tests, state, and logs exist.
    """
    # Define the project root (assumed to be the parent of 'code' or current dir if run from root)
    # We assume this script is run from the project root.
    root = Path.cwd()

    # Define required directories relative to root
    directories = [
        "code",
        "code/utils",
        "data/raw",
        "data/raw/repos",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "state",
        "logs"
    ]

    created_count = 0
    skipped_count = 0

    print(f"Setting up project structure at: {root}")

    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            # Check if it is actually a directory
            if full_path.is_dir():
                skipped_count += 1
            else:
                print(f"ERROR: Path exists but is not a directory: {dir_path}")
                return 1

    print(f"\nSetup complete. Created {created_count} directories, skipped {skipped_count} existing.")
    return 0

if __name__ == "__main__":
    sys.exit(main())