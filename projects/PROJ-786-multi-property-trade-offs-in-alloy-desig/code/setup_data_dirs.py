"""
Script to setup the data directory structure for the project.
Creates data/raw and data/processed directories with .gitkeep files.
"""
import os
from pathlib import Path

def setup_data_directories():
    """
    Creates the required data directory structure:
    - data/raw
    - data/processed

    Ensures .gitkeep files are present in each directory to track them in version control.
    """
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    # Create directories if they don't exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Create .gitkeep files to ensure directories are tracked by git
    (raw_dir / ".gitkeep").touch(exist_ok=True)
    (processed_dir / ".gitkeep").touch(exist_ok=True)

    print(f"Created directory structure: {data_dir}")
    print(f"  - {raw_dir}")
    print(f"  - {processed_dir}")
    print("Added .gitkeep files to ensure directories are tracked by version control.")

if __name__ == "__main__":
    setup_data_directories()
