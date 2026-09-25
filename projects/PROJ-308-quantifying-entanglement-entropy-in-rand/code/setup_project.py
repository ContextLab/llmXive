"""
Project Initialization Script for PROJ-308.

This script creates the necessary directory structure for the
Quantifying Entanglement Entropy in Randomly Perturbed Quantum Spin Chains project.

It ensures the following directory hierarchy exists relative to the project root:
- code/
- data/
  - raw/
  - processed/
- state/
  - projects/
- tests/
  - unit/
  - integration/
- docs/
- tools/
"""

import os
import sys
from pathlib import Path


def create_directory_structure():
    """Create the required project directory structure."""
    # Define the base project directory
    # The script is expected to be run from the project root or a parent directory
    # We assume the current working directory is the project root for simplicity
    # or we can determine it based on the script's location relative to 'code/'
    
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    project_root = code_dir.parent

    base_dirs = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "state",
        "state/projects",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs",
        "tools"
    ]

    created_dirs = []
    failed_dirs = []

    for dir_path in base_dirs:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
        except OSError as e:
            failed_dirs.append((str(full_path), str(e)))

    return created_dirs, failed_dirs


def main():
    """Main entry point for the setup script."""
    print(f"Initializing project structure in: {Path(__file__).resolve().parent.parent}")
    
    created, failed = create_directory_structure()

    if created:
        print("Successfully created directories:")
        for d in created:
            print(f"  - {d}")
    
    if failed:
        print("Failed to create directories:")
        for d, err in failed:
            print(f"  - {d}: {err}")
        sys.exit(1)
    
    print("Project structure initialization complete.")
    return 0


if __name__ == "__main__":
    sys.exit(main())