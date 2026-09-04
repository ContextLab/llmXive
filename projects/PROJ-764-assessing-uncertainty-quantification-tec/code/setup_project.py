"""
Project Setup Script for PROJ-764-assessing-uncertainty-quantification-tec

This script initializes the project directory structure as defined in Task T001a.
It creates the following directories relative to the project root:
- code/
- data/
- results/
- tests/
- docs/

It also ensures parent directories exist to support nested structures used by the pipeline.
"""
import os
from pathlib import Path


def main():
    """Create the standard project directory structure."""
    # Define the project root (assumed to be the directory containing this script's parent,
    # or we assume the script is run from the project root).
    # Based on task description, paths are relative to project root.
    project_root = Path(os.getcwd())

    # Define required directories
    directories = [
        "code",
        "data",
        "results",
        "tests",
        "docs",
        # Subdirectories required by later tasks (T005, T006, etc.)
        "data/raw",
        "data/processed",
        "results/models",
        "results/models/ensemble",
        "results/models/mc_dropout",
        "results/models/sparse_gp",
        "logs",
        "specs",
        "contracts",
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

    print(f"\nSetup complete. Created {created_count} new directories.")
    return 0


if __name__ == "__main__":
    exit(main())