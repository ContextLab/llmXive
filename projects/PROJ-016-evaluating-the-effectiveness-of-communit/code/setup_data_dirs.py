"""
Task T004: Setup data and output directories.

Creates the required directory structure for the project:
- data/raw/
- data/processed/
- docs/output/

This script ensures that all necessary directories exist before
data ingestion and analysis tasks begin.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the required data and output directories."""
    # Define the project root (assuming script is in code/)
    project_root = Path(__file__).resolve().parent.parent
    
    # Define directories to create
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "docs" / "output",
    ]
    
    # Create directories
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"Setup complete. Created {created_count} new directories.")
    
    # Verify all directories exist
    all_exist = all(directory.exists() for directory in directories)
    if all_exist:
        print("Verification: All required directories exist.")
        return 0
    else:
        print("Error: Some directories failed to be created.")
        return 1

if __name__ == "__main__":
    sys.exit(main())