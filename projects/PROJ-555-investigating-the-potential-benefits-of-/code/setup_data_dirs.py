"""
Script to create the required data directory structure and .gitkeep files.
This ensures version control tracks empty directories and prepares the project
for data ingestion.
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

    Creates .gitkeep files in each to ensure they are tracked by git.
    """
    # Define the required directories
    base_dir = Path("data")
    required_dirs = [
        base_dir / "raw" / "landsat",
        base_dir / "processed",
        base_dir / "ecotourism"
    ]

    # Use the existing ensure_directories utility
    ensure_directories(required_dirs)

    # Create .gitkeep files in each directory
    for dir_path in required_dirs:
        gitkeep_path = dir_path / ".gitkeep"
        # Ensure parent exists before creating file
        gitkeep_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create the file if it doesn't exist, or touch it to update timestamp
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created: {gitkeep_path}")
        else:
            print(f"Already exists: {gitkeep_path}")

    print("Data directory structure setup complete.")


if __name__ == "__main__":
    main()
