"""
Script to create the required data directory structure.
Creates data/raw/, data/processed/, and data/reports/ directories.
"""
import os
from pathlib import Path
from config import PROJECT_ROOT

def create_data_directories():
    """Create the data directory structure as specified in T001c."""
    data_root = Path(PROJECT_ROOT) / "data"
    directories = [
        data_root / "raw",
        data_root / "processed",
        data_root / "reports"
    ]

    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

    return data_root

if __name__ == "__main__":
    root = create_data_directories()
    print(f"Data structure created at: {root}")
