"""
Setup script to initialize the data directory structure.
Creates data/raw/ and data/processed/ directories.
"""
import os
from pathlib import Path

def setup_data_directories():
    """Create the required data directory structure."""
    base_path = Path(__file__).resolve().parent.parent
    data_dir = base_path / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    # Create directories if they don't exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Create .gitkeep files to ensure directories are tracked by git
    (raw_dir / ".gitkeep").touch()
    (processed_dir / ".gitkeep").touch()

    print(f"Created directory: {raw_dir}")
    print(f"Created directory: {processed_dir}")
    return True

if __name__ == "__main__":
    setup_data_directories()
