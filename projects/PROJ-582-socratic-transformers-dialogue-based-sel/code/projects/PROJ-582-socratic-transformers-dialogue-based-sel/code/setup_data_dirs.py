"""
Data Directory Structure Setup for PROJ-582-socratic-transformers-dialogue-based-sel

This module creates the required data directory structure at the project root:
- data/raw/
- data/processed/
- data/results/

It also creates .gitkeep files in each directory to ensure they are tracked by git.
"""

import os
import sys
from pathlib import Path


def setup_data_directories(base_path: Path) -> bool:
    """
    Create the data directory structure.

    Args:
        base_path: The project root path where 'data/' will be created.

    Returns:
        True if all directories were created successfully, False otherwise.
    """
    data_path = base_path / "data"
    directories = [
        data_path / "raw",
        data_path / "processed",
        data_path / "results",
    ]

    success = True
    for dir_path in directories:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            # Create .gitkeep to ensure directory is tracked by git
            gitkeep_path = dir_path / ".gitkeep"
            gitkeep_path.touch(exist_ok=True)
            print(f"Created: {dir_path}")
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
            success = False

    return success


def create_gitkeep(base_path: Path) -> bool:
    """
    Ensure .gitkeep files exist in all data subdirectories.

    Args:
        base_path: The project root path.

    Returns:
        True if all .gitkeep files were created/verified, False otherwise.
    """
    data_path = base_path / "data"
    if not data_path.exists():
        print(f"Error: {data_path} does not exist. Run setup_data_directories first.", file=sys.stderr)
        return False

    directories = ["raw", "processed", "results"]
    success = True

    for subdir in directories:
        dir_path = data_path / subdir
        gitkeep_path = dir_path / ".gitkeep"
        try:
            if not gitkeep_path.exists():
                gitkeep_path.touch()
                print(f"Created .gitkeep in {dir_path}")
            else:
                print(f".gitkeep already exists in {dir_path}")
        except OSError as e:
            print(f"Error creating .gitkeep in {dir_path}: {e}", file=sys.stderr)
            success = False

    return success


def main() -> int:
    """
    Main entry point for the script.

    Creates the data directory structure at the project root.
    """
    # Determine project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    print(f"Project root: {project_root}")
    print("Setting up data directory structure...")

    if setup_data_directories(project_root):
        print("Data directory structure created successfully.")
        return 0
    else:
        print("Failed to create data directory structure.", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())