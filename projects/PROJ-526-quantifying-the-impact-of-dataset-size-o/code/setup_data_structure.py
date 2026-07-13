"""
Task T004: Create `data/` directory structure (`raw/`, `processed`) and `state/` for checksums.

This script creates the necessary directory hierarchy for the project's data
and state management as defined in the project plan.

It relies on `code/setup_directories.py` for the core creation logic.
"""
import os
from pathlib import Path
from setup_directories import create_directories

def main():
    """
    Creates the required directory structure for data and state.
    
    Directories created (relative to project root):
    - data/raw/
    - data/processed/
    - state/
    """
    # Define the base paths relative to the project root
    # Assuming this script runs from the project root or code/ directory
    # We use a relative path strategy that works from the repo root.
    
    # If running from code/, we need to go up one level to reach the project root
    # However, the task description implies standard paths from root.
    # Let's assume the script is invoked from the root or handles paths relative to itself.
    
    # Strategy: Determine project root (parent of 'code' folder)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    # Define relative paths to create
    relative_paths = [
        "data/raw",
        "data/processed",
        "state"
    ]
    
    created_paths = []
    for rel_path in relative_paths:
        full_path = project_root / rel_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    # Verify creation
    missing = []
    for rel_path in relative_paths:
        full_path = project_root / rel_path
        if not full_path.exists():
            missing.append(str(full_path))
    
    if missing:
        raise RuntimeError(f"Failed to create directories: {missing}")
    
    print("Directory structure setup complete.")
    return True

if __name__ == "__main__":
    main()