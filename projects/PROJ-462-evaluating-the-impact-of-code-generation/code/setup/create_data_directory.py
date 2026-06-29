"""
Create data directory structure for the project.

Creates:
  - data/
  - data/raw/
  - data/processed/
  - data/output/

Usage:
  python code/setup/create_data_directory.py
"""
import os
import sys
from pathlib import Path


def create_data_directory():
    """Create the data directory structure."""
    project_root = Path(__file__).parent.parent.parent
    data_dir = project_root / "data"
    
    subdirectories = ["raw", "processed", "output"]
    
    # Create base data directory
    data_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {data_dir}")
    
    # Create subdirectories
    for subdir in subdirectories:
        subdir_path = data_dir / subdir
        subdir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {subdir_path}")
    
    return True


def main():
    """Entry point for script execution."""
    print("Creating data directory structure...")
    
    success = create_data_directory()
    
    if success:
        print("\nData directory structure created successfully.")
        print("Directories created:")
        print("  - data/raw/")
        print("  - data/processed/")
        print("  - data/output/")
        return 0
    else:
        print("\nFailed to create data directory structure.")
        return 1


if __name__ == "__main__":
    sys.exit(main())