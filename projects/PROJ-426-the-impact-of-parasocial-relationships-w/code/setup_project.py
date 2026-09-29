import os
import sys
from pathlib import Path

def main():
    """
    Create the project root directory structure for PROJ-426.
    
    Creates the following directories relative to the project root:
    - src/
    - tests/
    - data/
    - data/raw/
    - data/processed/
    - data/results/
    - docs/
    - contracts/
    - config/
    """
    # Determine project root (assumes script is run from project root or one level up)
    # We use the directory containing this script as the reference point for safety,
    # but typically this runs from the repo root.
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent if script_dir.name == 'code' else script_dir

    # Define the required directory structure
    directories = [
        "src",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "docs",
        "contracts",
        "config"
    ]

    created_count = 0
    for dir_name in directories:
        target_path = project_root / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {target_path}")

    print(f"\nProject structure initialization complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())