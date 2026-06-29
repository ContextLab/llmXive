"""Create the data/raw directory for the atmospheric river gravity correlation project.

This script creates the data/raw directory structure as specified in task T003.
The directory is used to store raw downloaded datasets (GRACE-FO mascon solutions
and NOAA CPC Atmospheric River Catalog data) before preprocessing.
"""

import os
from pathlib import Path


def ensure_data_raw_directory():
    """Create the data/raw directory if it doesn't exist.

    Returns:
        Path: The path to the created data/raw directory.
    """
    # Project root is parent of code/ directory
    project_root = Path(__file__).resolve().parent.parent
    data_raw_dir = project_root / "data" / "raw"
    data_raw_dir.mkdir(parents=True, exist_ok=True)
    return data_raw_dir


def main():
    """Main entry point: create the data/raw directory and report success."""
    data_raw_dir = ensure_data_raw_directory()
    print(f"Created data/raw directory at: {data_raw_dir}")
    print(f"Directory exists: {data_raw_dir.exists()}")
    print(f"Is directory: {data_raw_dir.is_dir()}")


if __name__ == "__main__":
    main()
