"""
Project Structure Creation Script.

This module provides functionality to create the required directory structure
for the PROJ-558-consciousness-bootstrapping-self-aware-a project.
"""
import os
from pathlib import Path


def create_structure(base_dir: str = "projects/PROJ-558-consciousness-bootstrapping-self-aware-a") -> None:
    """
    Create the directory structure for the project.

    Creates the following hierarchy relative to the current working directory:
    - data/raw
    - data/processed
    - code
    - tests
    - artifacts
    - artifacts/checkpoints
    - artifacts/reports

    Args:
        base_dir: The base directory path for the project structure.
    """
    project_path = Path(base_dir)

    # Define all required subdirectories
    subdirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts",
        "artifacts/checkpoints",
        "artifacts/reports",
    ]

    created_dirs = []
    for subdir in subdirs:
        full_path = project_path / subdir
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path))

    print(f"Created project structure at: {project_path}")
    for d in created_dirs:
        print(f"  - {d}")


def main() -> None:
    """Entry point for the script."""
    create_structure()


if __name__ == "__main__":
    main()
