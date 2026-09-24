"""
Project Directory Structure Initialization Script.

This script creates the required directory structure for the
PROJ-413-predicting-molecular-interactions-in-pol project.
"""

import os
import sys
from pathlib import Path


def main():
    """Create the project directory structure."""
    # Define the project root
    project_root = Path(__file__).resolve().parent.parent
    project_name = "PROJ-413-predicting-molecular-interactions-in-pol"
    project_path = project_root / project_name

    # If the project path doesn't exist, create it
    if not project_path.exists():
        project_path.mkdir(parents=True)
        print(f"Created project root: {project_path}")

    # Define the directories to create
    directories = [
        "data/raw",
        "data/curated",
        "data/processed",
        "code/data",
        "code/models",
        "code/analysis",
        "code/utils",
        "results",
        "analysis",
        "docs",
        "tests/contract",
        "tests/integration",
    ]

    # Create each directory
    for dir_path in directories:
        full_path = project_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Verify the structure
    print("\nVerifying directory structure...")
    all_exist = True
    for dir_path in directories:
        full_path = project_path / dir_path
        if not full_path.exists():
            print(f"ERROR: Missing directory: {full_path}")
            all_exist = False
        else:
            print(f"  [OK] {dir_path}")

    if all_exist:
        print("\n✓ All directories created successfully.")
        return 0
    else:
        print("\n✗ Some directories failed to create.")
        return 1


if __name__ == "__main__":
    sys.exit(main())