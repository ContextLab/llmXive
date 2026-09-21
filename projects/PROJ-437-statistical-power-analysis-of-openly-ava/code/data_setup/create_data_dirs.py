"""
Module to create the required data directory structure for the project.
Implements T001c.
"""
import os
import sys
from pathlib import Path


def create_data_directories(base_path: Optional[Path] = None) -> list:
    """
    Creates the standard data directory hierarchy.

    Creates:
      - data/
      - data/raw/
      - data/derived/
      - data/aggregated/

    Args:
        base_path: Optional base path. Defaults to project root (parent of code/).

    Returns:
        List of created Path objects.
    """
    if base_path is None:
        # Default to project root (assuming this script is in code/data_setup/)
        base_path = Path(__file__).resolve().parent.parent.parent

    data_root = base_path / "data"
    directories = [
        data_root,
        data_root / "raw",
        data_root / "derived",
        data_root / "aggregated",
    ]

    created = []
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    return created


def main():
    """Entry point for command-line execution."""
    print("Creating data directories...")
    try:
        created_dirs = create_data_directories()
        print(f"Successfully created {len(created_dirs)} directories.")
        return 0
    except Exception as e:
        print(f"Error creating directories: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
