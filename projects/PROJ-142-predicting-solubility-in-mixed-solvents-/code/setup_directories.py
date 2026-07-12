"""
Script to initialize the project directory structure for the solubility prediction pipeline.

This script creates the required directories as defined in task T001:
- code/ (already exists, but ensures root)
- data/raw/
- data/processed/
- data/artifacts/
- tests/
- specs/001-predicting-solubility-in-mixed-solvents/contracts/

Usage:
    python code/setup_directories.py
"""

import os
import sys
from pathlib import Path


def main():
    # Define the project root (parent of the code/ directory where this script lives)
    # Assuming this script is run as: python code/setup_directories.py
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Define relative paths to create
    directories = [
        "data/raw",
        "data/processed",
        "data/artifacts",
        "tests",
        "specs/001-predicting-solubility-in-mixed-solvents/contracts",
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
            existing_count += 1

    print(f"\nSetup complete. Created {created_count} directories, {existing_count} already existed.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
