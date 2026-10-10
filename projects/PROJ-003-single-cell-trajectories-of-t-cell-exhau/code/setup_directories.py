"""Establish the required directory structure for the T-cell exhaustion project.

This script creates the base layout defined in the project plan to ensure
that data loaders, preprocessing scripts, and result generators have
consistent paths to write to.
"""
import os
from pathlib import Path

def setup_directories() -> Path:
    """Create the required directory structure for the project.

    Creates the following directories relative to the project root:
    - code/
    - data/raw/
    - data/processed/
    - data/results/
    - tests/unit/
    - tests/integration/

    Returns:
        Path: The project root path where directories were created.
    """
    # Project root is the parent of the 'code' directory
    project_root = Path(__file__).resolve().parent.parent

    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests/unit",
        "tests/integration",
    ]

    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directories are present in the filesystem
        # and visible to the environment collector.
        (full_path / ".gitkeep").touch()

    return project_root

if __name__ == "__main__":
    root = setup_directories()
    print(f"Project layout established at: {root}")
