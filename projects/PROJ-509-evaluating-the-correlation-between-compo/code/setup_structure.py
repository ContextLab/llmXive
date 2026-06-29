import os
import sys
from pathlib import Path

def main():
    """
    Creates the required data directory structure for the project.
    
    This function ensures the following directories exist under the project root:
    - data/raw
    - data/elemental_properties
    - data/processed
    - data/evaluation
    - data/logs
    
    This task (T004) is a re-implementation of the directory creation logic
    to ensure it exists as a standalone executable script if T001's shell command
    was insufficient or if the environment requires a Python-based setup.
    """
    # Determine project root based on the location of this script
    # Assuming this script is in code/
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent
    
    # Define the data directory structure
    data_dirs = [
        "data/raw",
        "data/elemental_properties",
        "data/processed",
        "data/evaluation",
        "data/logs"
    ]
    
    created_count = 0
    for dir_path in data_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    if created_count == 0:
        print("All data directories already exist.")
    else:
        print(f"Successfully created {created_count} new directory(ies).")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())