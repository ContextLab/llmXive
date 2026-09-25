"""
Setup script to initialize the data directory structure for the CMB analysis project.
Creates raw and processed data directories as per project specifications.
"""
import os
from pathlib import Path

def main():
    """
    Creates the required data directory structure:
    - data/raw/
    - data/processed/
    
    Also initializes __init__.py files in these directories to mark them as Python packages.
    """
    base_path = Path(__file__).resolve().parent.parent
    data_root = base_path / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"

    # Create directories if they don't exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)

    # Create __init__.py files to mark as packages
    (raw_dir / "__init__.py").touch()
    (processed_dir / "__init__.py").touch()

    print(f"Created data directory structure:")
    print(f"  - {raw_dir}")
    print(f"  - {processed_dir}")

if __name__ == "__main__":
    main()
