"""
Script to initialize data directories with .gitkeep files.
This task (T008) ensures data/raw and data/processed directories exist
and contain .gitkeep files to preserve directory structure in git.
"""
import os
from pathlib import Path
from config import ensure_directories


def main():
    """
    Create data directories and .gitkeep files.
    """
    # Ensure the standard data directories exist
    # This calls the function from config.py which creates the dirs
    ensure_directories()

    # Define the paths for .gitkeep files
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")

    # Create .gitkeep files if they don't exist
    raw_keep = raw_dir / ".gitkeep"
    processed_keep = processed_dir / ".gitkeep"

    if not raw_keep.exists():
        raw_keep.touch()
        print(f"Created {raw_keep}")
    else:
        print(f"{raw_keep} already exists")

    if not processed_keep.exists():
        processed_keep.touch()
        print(f"Created {processed_keep}")
    else:
        print(f"{processed_keep} already exists")

    print("Data directory initialization complete.")


if __name__ == "__main__":
    main()
