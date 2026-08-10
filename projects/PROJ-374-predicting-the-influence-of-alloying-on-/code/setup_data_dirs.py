"""
Setup script to create the data directory structure for the project.
Creates data/raw/ and data/processed/ directories.
"""
import os
from pathlib import Path

def main():
    # Determine the project root (assuming this script is in code/)
    project_root = Path(__file__).resolve().parent.parent
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    # Create directories if they don't exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Create .gitkeep files to ensure directories are tracked by git
    (raw_dir / ".gitkeep").touch()
    (processed_dir / ".gitkeep").touch()

    print(f"Created directories:")
    print(f"  {raw_dir}")
    print(f"  {processed_dir}")

if __name__ == "__main__":
    main()