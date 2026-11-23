"""
Script to create the required data directory structure for the project.
Creates data/raw/, data/intermediate/, and data/processed/ subdirectories.
"""
import os
from pathlib import Path


def create_data_directories(base_path: str = ".") -> None:
    """
    Create the standard data directory structure.

    Args:
        base_path: The root directory where 'data' folder exists (default: current directory)
    """
    base = Path(base_path)
    data_dir = base / "data"

    # Ensure the main data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)

    # Define subdirectories
    subdirs = [
        "raw",
        "intermediate",
        "processed"
    ]

    for subdir_name in subdirs:
        subdir_path = data_dir / subdir_name
        subdir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {subdir_path}")

    print("Data directory structure setup complete.")


def main() -> None:
    """Entry point for the script."""
    create_data_directories()


if __name__ == "__main__":
    main()