"""
Create data directory structure for the statistical analysis project.

This script creates the required directory hierarchy under data/:
  - data/raw/          : Raw data from external sources (GitHub API)
  - data/processed/    : Cleaned and processed datasets ready for analysis
  - data/figures/      : Generated plots, charts, and visualizations

Usage:
    python code/setup/create_data_dirs.py

Output:
    Creates directory structure and prints confirmation.
"""

import os
from pathlib import Path


def create_data_directories(base_dir: Path = None) -> None:
    """
    Create the data directory structure.

    Args:
        base_dir: Base directory for the project. Defaults to project root
                 (parent of code/ directory).
    """
    if base_dir is None:
        # Default to project root (parent of code/ directory)
        script_path = Path(__file__).resolve()
        base_dir = script_path.parent.parent

    # Define the data directory structure
    data_dirs = [
        base_dir / "data",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "figures",
    ]

    # Create each directory
    created_count = 0
    for dir_path in data_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {dir_path.relative_to(base_dir)}")
            created_count += 1
        else:
            print(f"Exists:  {dir_path.relative_to(base_dir)}")

    print(f"\nData directory structure ready. {created_count} new directories created.")


if __name__ == "__main__":
    create_data_directories()
