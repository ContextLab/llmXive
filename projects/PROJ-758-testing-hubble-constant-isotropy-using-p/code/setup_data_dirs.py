"""
Script to initialize the project data directory structure.

This script creates the necessary directory hierarchy for the Hubble Constant
Isotropy analysis project, ensuring that data storage follows the standard
convention:

- data/raw:   For unmodified, downloaded source data (e.g., Pantheon+ CSV)
- data/processed: For cleaned, filtered, and spatially indexed datasets
- data/results: For final analysis outputs, plots, and reports

This corresponds to Task T003 in the project plan.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine the project root relative to this script location
    # The script is located at code/setup_data_dirs.py
    # We expect the project root to be the parent of the 'code' directory
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    data_dir = project_root / "data"
    
    directories = [
        data_dir / "raw",
        data_dir / "processed",
        data_dir / "results",
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Initializing data directories for project at: {project_root}")
    
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created: {directory}")
            created_count += 1
        else:
            # Check if it is actually a directory
            if directory.is_dir():
                print(f"Exists: {directory}")
                existing_count += 1
            else:
                print(f"ERROR: Path exists but is not a directory: {directory}")
                return 1
    
    print(f"Data structure initialization complete. Created: {created_count}, Existing: {existing_count}")
    return 0

if __name__ == "__main__":
    sys.exit(main())