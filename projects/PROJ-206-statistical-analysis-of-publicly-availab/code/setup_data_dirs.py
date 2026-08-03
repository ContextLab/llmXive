"""
Setup script to create the required data directory structure for the project.

Creates the following directories relative to the project root:
- data/raw/
- data/processed/
- state/projects/

This script is idempotent: it will not fail if directories already exist.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the data directory structure."""
    # Determine project root (assuming this script is in code/ or code/code/)
    # We traverse up to find the root where 'data' and 'state' should be created.
    current_path = Path(__file__).resolve()
    
    # Heuristic: if we are in code/code/, go up two levels. If in code/, go up one.
    # To be safe, we look for the 'data' directory relative to common roots.
    # Standard assumption: Project root is the parent of 'code', 'data', 'state'.
    project_root = current_path.parent.parent if current_path.name == 'setup_data_dirs.py' and current_path.parent.name == 'code' else current_path.parent
    
    # If the heuristic fails (e.g. running from a different structure), 
    # we default to the current working directory if 'data' doesn't exist nearby.
    if not (project_root / 'data').exists() and not (project_root / 'state').exists():
        # Try one level up if we are deep in code/code
        if current_path.parent.name == 'code' and current_path.parent.parent.name == 'code':
            project_root = current_path.parent.parent.parent
        
        # Fallback to cwd if still not found
        if not (project_root / 'data').exists():
            project_root = Path.cwd()

    print(f"Project root detected at: {project_root}")

    # Define directories
    data_raw = project_root / 'data' / 'raw'
    data_processed = project_root / 'data' / 'processed'
    state_projects = project_root / 'state' / 'projects'

    directories = [data_raw, data_processed, state_projects]

    created = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created += 1
        else:
            print(f"Directory already exists: {directory}")

    print(f"Setup complete. {created} new directories created.")
    
    # Verify
    missing = [d for d in directories if not d.exists()]
    if missing:
        print(f"Error: Failed to create {missing}")
        sys.exit(1)
    else:
        print("All required directories verified.")

if __name__ == "__main__":
    main()
