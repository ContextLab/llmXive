"""
Data directory setup script for PROJ-786.
Creates the required raw and processed data subdirectories.
"""
import os
from pathlib import Path

def setup_data_directories():
    """
    Creates the `data/raw/` and `data/processed/` subdirectories.
    Ensures they exist for the data ingestion and processing pipeline.
    """
    # Determine project root (assuming script is run from root or code/)
    # We target the `data` directory relative to the current working directory
    # or explicitly relative to the script location if run as a module.
    # Standard practice: assume execution from project root.
    project_root = Path.cwd()
    data_root = project_root / "data"

    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"

    # Create directories if they don't exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Create .gitkeep files to ensure directories are tracked by git
    (raw_dir / ".gitkeep").touch()
    (processed_dir / ".gitkeep").touch()

    print(f"Created directories: {raw_dir}, {processed_dir}")
    return True

if __name__ == "__main__":
    setup_data_directories()
