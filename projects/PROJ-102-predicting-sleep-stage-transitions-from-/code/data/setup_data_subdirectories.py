"""
Task T001b: Create data/raw, data/processed, data/interim subdirectories.

This script ensures the required data directory structure exists within the project.
It creates the following directories relative to the project root:
- data/raw: For raw, unprocessed data (e.g., downloaded Sleep-EDF files)
- data/processed: For cleaned, segmented, and feature-extracted data
- data/interim: For intermediate data products during processing pipelines
"""
import os
from pathlib import Path
import sys

def main():
    """Create the required data subdirectories."""
    # Determine project root (assuming script is in code/ or code/data/)
    # We need to go up to the project root to create 'data/'
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent  # code/ -> project root
    
    data_dir = project_root / "data"
    
    # Define required subdirectories
    subdirs = [
        data_dir / "raw",
        data_dir / "processed",
        data_dir / "interim"
    ]
    
    created_count = 0
    for subdir in subdirs:
        if not subdir.exists():
            subdir.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {subdir}")
            created_count += 1
        else:
            print(f"Directory already exists: {subdir}")
    
    # Also ensure the parent data/ directory exists if subdirs didn't
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created parent directory: {data_dir}")
        created_count += 1
    
    if created_count == 0:
        print("All required data directories already exist.")
    else:
        print(f"Successfully created {created_count} directory/directories.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
