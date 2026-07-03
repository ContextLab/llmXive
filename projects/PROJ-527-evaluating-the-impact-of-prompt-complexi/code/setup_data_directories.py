"""
Data Directory Setup Utility.

Creates the required data directory structure for the project:
- data/raw/
- data/processed/
- data/results/
"""

import os
from pathlib import Path

# Project root is the parent of the 'code/' directory
_PROJECT_ROOT = Path(__file__).resolve().parent.parent


def create_data_directories() -> None:
    """
    Create the standard data directory structure if it does not exist.

    Directories created:
    - data/raw
    - data/processed
    - data/results
    """
    data_base = _PROJECT_ROOT / "data"
    directories = [
        data_base / "raw",
        data_base / "processed",
        data_base / "results",
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified directory: {directory}")


if __name__ == "__main__":
    create_data_directories()