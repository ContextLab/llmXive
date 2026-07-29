"""
Setup script for creating the required data directory structure.
This script ensures that `data/raw/` and `data/processed/` directories exist
relative to the project root.
"""
import os
from pathlib import Path
import sys

# Add the code directory to the path to import config if needed,
# though we can also derive root directly.
code_dir = Path(__file__).parent
project_root = code_dir.parent

def setup_data_directories():
    """Create the data/raw and data/processed directory structure."""
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    directories = [data_dir, raw_dir, processed_dir]

    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")

    print(f"Data directory structure setup complete at: {data_dir}")

if __name__ == "__main__":
    setup_data_directories()
