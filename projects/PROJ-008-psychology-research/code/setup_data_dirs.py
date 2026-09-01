"""
Setup script to create required data sub-directories for PROJ-008-psychology-research.

This script implements task T001b by creating the following directories:
- projects/PROJ-008-psychology-research/data/raw/
- projects/PROJ-008-psychology-research/data/processed/
- projects/PROJ-008-psychology-research/data/interim/

It ensures the directory structure exists for the research pipeline to store
raw data, processed data, and interim data files.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the required data sub-directories."""
    # Determine project root based on script location
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent.parent  # Go up to project root
    
    # Define the data directories to create
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "interim",
    ]
    
    # Create directories
    created_count = 0
    for dir_path in data_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nData directory setup complete. {created_count} new directories created.")
    
    # Verify all directories exist
    all_exist = all(dir_path.exists() and dir_path.is_dir() for dir_path in data_dirs)
    if not all_exist:
        print("ERROR: Not all required directories were created successfully.")
        sys.exit(1)
    
    print("All required data directories verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
