#!/usr/bin/env python3
"""
Project Scaffolding Script for PROJ-592: Phenomenological AI First-Person Experience Modeling.

This script initializes the directory structure required for the research pipeline,
creating folders for code, raw/processed/qualitative data, tests, and specifications.

Execution:
    python scripts/init_project.py
"""

import os
import sys
from pathlib import Path


def create_directories(base_path: Path) -> None:
    """
    Creates the required directory structure relative to the project root.

    Args:
        base_path: The root directory of the project (parent of 'scripts').
    """
    # Define the relative paths to be created
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/qualitative",
        "tests/unit",
        "tests/integration",
        "specs/contracts",
    ]

    created_count = 0
    skipped_count = 0

    for dir_name in directories:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"[CREATED] {full_path}")
            created_count += 1
        else:
            print(f"[SKIPPED] {full_path} (already exists)")
            skipped_count += 1

    print(f"\nScaffolding complete: {created_count} directories created, {skipped_count} skipped.")


def main() -> int:
    """
    Entry point for the script.
    Determines the project root based on the script's location and creates directories.
    """
    # Determine the project root: parent of the 'scripts' directory
    current_file = Path(__file__).resolve()
    if current_file.parent.name != "scripts":
        print("Error: This script must be located in a 'scripts' directory at the project root.")
        return 1

    project_root = current_file.parent.parent

    print(f"Project Root detected: {project_root}")
    print("Initializing directory structure...\n")

    create_directories(project_root)

    # Verify creation
    required_dirs = [
        "code", "data/raw", "data/processed", "data/qualitative",
        "tests/unit", "tests/integration", "specs/contracts"
    ]
    missing = [d for d in required_dirs if not (project_root / d).exists()]

    if missing:
        print(f"\nError: The following directories were not created: {missing}")
        return 1

    print("\nAll required directories verified successfully.")
    return 0


if __name__ == "__main__":
    sys.exit(main())