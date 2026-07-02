"""
Setup script for data directory structure.
Creates 'data/raw' and 'data/processed' directories as required by the project.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to this script location
    # The script is at code/utils/setup_data_dirs.py
    # So project root is two levels up
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    consent_dir = data_dir / "consent"

    # Create directories
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    consent_dir.mkdir(parents=True, exist_ok=True)

    # Create .gitkeep files to ensure directories are tracked by git
    (raw_dir / ".gitkeep").touch()
    (processed_dir / ".gitkeep").touch()
    (consent_dir / ".gitkeep").touch()

    print(f"Data directories created successfully:")
    print(f"  - {raw_dir}")
    print(f"  - {processed_dir}")
    print(f"  - {consent_dir}")

if __name__ == "__main__":
    main()