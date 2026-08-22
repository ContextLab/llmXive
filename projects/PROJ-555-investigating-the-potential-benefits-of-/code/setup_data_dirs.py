"""
Setup script to create the required data directory structure.
This script creates directories and .gitkeep files to ensure
the directory structure is preserved in version control.
"""
import os
from pathlib import Path
from config import ensure_directories

def main():
    """
    Creates the data directory structure:
    - data/raw/landsat
    - data/processed
    - data/ecotourism

    Also creates .gitkeep files in each directory to ensure
    they are tracked by git.
    """
    # Define the directories to create
    data_dirs = [
        "data/raw/landsat",
        "data/processed",
        "data/ecotourism"
    ]

    # Use the existing ensure_directories utility
    ensure_directories(data_dirs)

    # Create .gitkeep files in each directory
    for dir_path in data_dirs:
        gitkeep_path = Path(dir_path) / ".gitkeep"
        gitkeep_path.touch()
        print(f"Created {gitkeep_path}")

    print("Data directory structure created successfully.")

if __name__ == "__main__":
    main()