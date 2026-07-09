import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in the implementation plan.
    Directories created relative to the repository root (where this script is run).
    """
    # Define the required directories relative to the current working directory
    # which should be the project root.
    directories = [
        "data/raw",
        "data/processed",
        "data/results",
        "code",
        "tests",
        "state"
    ]

    project_root = Path.cwd()
    created_count = 0

    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {full_path}")
                created_count += 1
            else:
                # Ensure it is actually a directory, not a file
                if full_path.is_dir():
                    print(f"Directory already exists: {full_path}")
                else:
                    print(f"ERROR: Path exists but is not a directory: {full_path}")
                    return 1
        except OSError as e:
            print(f"ERROR: Failed to create directory {full_path}: {e}")
            return 1

    print(f"Project structure initialization complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())