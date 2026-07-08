"""
Setup script for data directory structure.
Creates data/raw and data/processed directories with .gitkeep files.
"""
import os
from pathlib import Path

def setup_data_directories():
    """Create required data directory structure if they don't exist."""
    project_root = Path(__file__).parent.parent
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    # Create directories
    for directory in [data_dir, raw_dir, processed_dir]:
        directory.mkdir(parents=True, exist_ok=True)
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created: {gitkeep_path}")
        else:
            print(f"Already exists: {gitkeep_path}")

    print(f"Data directory structure ready at: {data_dir}")

if __name__ == "__main__":
    setup_data_directories()