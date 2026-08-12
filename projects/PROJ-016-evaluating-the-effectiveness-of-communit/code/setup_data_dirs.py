import os
import sys
from pathlib import Path

def main():
    """
    T004: Setup data directories and output directories.
    Creates the following directories relative to the project root:
    - data/raw/
    - data/processed/
    - docs/output/
    """
    # Determine project root (assuming code/ is in project root)
    # If run from command line: python code/setup_data_dirs.py
    # We need to resolve paths relative to the script's parent directory (project root)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent

    dirs_to_create = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "docs" / "output",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    if created_count > 0:
        print(f"Successfully created {created_count} new directories.")
    else:
        print("All required directories already existed.")

    return 0

if __name__ == "__main__":
    sys.exit(main())
