import os
import sys
from pathlib import Path

def main():
    """
    Creates the required project directory structure as defined in plan.md and tasks.md.
    Directories created:
      - code/
      - data/raw/
      - data/processed/
      - tests/
      - artifacts/reports/
      - artifacts/figures/
      - state/
    """
    # Define the project root (current working directory)
    project_root = Path.cwd()

    # Define the relative paths to be created
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "artifacts/reports",
        "artifacts/figures",
        "state"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            # Verify it is actually a directory
            if full_path.is_dir():
                print(f"Directory already exists: {full_path}")
            else:
                print(f"ERROR: Path exists but is not a directory: {full_path}")
                return 1

    print(f"Project structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())