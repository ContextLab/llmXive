"""
Script to initialize the project directory structure for PROJ-405.
This script creates the necessary subdirectories under the project root.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine project root relative to this script's location
    # Assuming this script is at projects/PROJ-405/setup_dirs.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parent

    dirs_to_create = [
        "code",
        "data",
        "tests",
        "artifacts",
        "specs/001-predict-plant-disease-severity/contracts",
        "data/raw",
        "data/processed",
        "data/external",
        "figures",
        "state",
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")

    # Ensure __init__.py files exist for Python packages
    init_dirs = ["code", "data", "tests", "artifacts"]
    for d in init_dirs:
        init_file = project_root / d / "__init__.py"
        if not init_file.exists():
          init_file.write_text(f'"""\n{d.upper()} package for PROJ-405.\n"""\n')
          print(f"Created init: {init_file}")

    print(f"\nProject structure initialization complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())