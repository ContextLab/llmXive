"""
T004: Setup data directory structure.
Creates the required directories for raw data, processed data, and project state.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Creates the following directory structure relative to the project root:
    - data/raw/
    - data/processed/
    - state/projects/
    """
    # Determine project root (assuming this script is at code/setup_data_structure.py)
    # We go up two levels to get to the root if run from the script location,
    # or rely on the current working directory if run as a module.
    # To be robust, we assume the script is run from the project root or
    # we define the root relative to this file's location.
    
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent  # Assuming code/ is at root level based on tasks.md structure

    # Define paths
    data_root = project_root / "data"
    state_root = project_root / "state"

    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    projects_dir = state_root / "projects"

    directories = [
        data_root,
        raw_dir,
        processed_dir,
        state_root,
        projects_dir
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")

    print(f"\nSetup complete. Created/Verified {created_count} new directories.")
    print(f"Data Root: {data_root}")
    print(f"State Root: {state_root}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
