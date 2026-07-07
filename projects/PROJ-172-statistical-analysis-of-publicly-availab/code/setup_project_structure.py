import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure as defined in the plan.
    Directories created:
    - code/
    - data/raw/
    - data/processed/
    - tests/
    - artifacts/reports/
    - artifacts/figures/
    - state/
    """
    # Determine project root (assuming this script is in code/, root is parent)
    # However, to be robust, we assume the script is run from the project root
    # or we calculate relative to this file's location.
    # Standard convention: run from root.
    project_root = Path.cwd()

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
            print(f"Directory already exists: {full_path}")

    print(f"Project structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
