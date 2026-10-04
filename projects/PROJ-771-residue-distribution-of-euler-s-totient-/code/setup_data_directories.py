"""
Setup script to create the raw and processed data directories.
This script ensures the directory structure required for storing
raw residue data and processed statistical results exists.
"""
import os
from pathlib import Path


def setup_data_directories():
    """
    Creates the 'data/raw' and 'data/processed' directories if they do not exist.
    Prints confirmation messages for each created directory.
    """
    base_path = Path("data")
    raw_path = base_path / "raw"
    processed_path = base_path / "processed"

    directories = [raw_path, processed_path]

    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

    return True


if __name__ == "__main__":
    setup_data_directories()