"""
Script to set up the data directory structure for the molecular properties project.
Creates the required directories: raw/, preprocessed/, and external/ under data/.
"""
import os
from pathlib import Path

def main():
    """Create the data directory structure."""
    # Define the root directory (project root)
    root = Path(__file__).resolve().parent.parent.parent
    data_dir = root / "data"

    # Define subdirectories
    subdirs = ["raw", "preprocessed", "external"]

    # Create directories
    for subdir in subdirs:
        dir_path = data_dir / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Data directory structure created at: {data_dir}")

if __name__ == "__main__":
    main()