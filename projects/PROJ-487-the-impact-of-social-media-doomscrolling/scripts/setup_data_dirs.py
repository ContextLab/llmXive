"""
Script to create required data directories for the project.

Creates the following directory structure under the project root:
- data/raw/
- data/processed/
- data/reports/

This script is idempotent and will not fail if directories already exist.
"""
import os
import sys
from pathlib import Path


def main():
    """Create the required data directories."""
    # Determine project root based on this script's location
    # The script is expected to be at: projects/PROJ-487-the-impact-of-social-media-doomscrolling/scripts/setup_data_dirs.py
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    # Define the data directories to create
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/reports"
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Project root: {project_root}")
    print("Creating data directories...")
    
    for dir_name in data_dirs:
        dir_path = project_root / dir_name
        
        if dir_path.exists():
            print(f"  [SKIP] {dir_path} already exists")
            skipped_count += 1
        else:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  [CREATE] {dir_path}")
            created_count += 1
    
    print(f"\nSummary: {created_count} directories created, {skipped_count} skipped.")
    
    # Verify all directories exist
    all_exist = all((project_root / d).exists() for d in data_dirs)
    if not all_exist:
        print("ERROR: Not all directories were created successfully.")
        sys.exit(1)
    
    print("All data directories are ready.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
