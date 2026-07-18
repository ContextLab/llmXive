"""
Project Directory Setup Script for PROJ-560-embodied-curriculum-learning-physical-si.

This script creates the required directory structure for the project,
including code, data, and state directories.
"""
import os
import sys
from pathlib import Path


def create_directory(path: str) -> bool:
    """
    Create a directory if it does not exist.

    Args:
        path: The path to the directory to create.

    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    dir_path = Path(path)
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False


def main() -> int:
    """
    Main function to create all required project directories.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    base_path = Path("projects/PROJ-560-embodied-curriculum-learning-physical-si")

    # Define all required directories
    directories = [
        # Code directories
        base_path / "code" / "src",
        base_path / "code" / "tests",
        
        # Data directories
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "synthetic",
        base_path / "data" / "derivation_logs",
        
        # State directories
        base_path / "state" / "projects" / "PROJ-560-embodied-curriculum-learning-physical-si",
    ]

    success = True
    for dir_path in directories:
        if create_directory(str(dir_path)):
            print(f"Created directory: {dir_path}")
        else:
            print(f"Failed to create directory: {dir_path}", file=sys.stderr)
            success = False

    return 0 if success else 1


if __name__ == "__main__":
    sys.exit(main())