"""
Setup script to create the required project directory structure.

This script ensures the existence of the following directories relative to the project root:
- data/raw/
- data/processed/
- state/
- code/

It is idempotent: running it multiple times will not cause errors if directories already exist.
"""
import os
import sys
from pathlib import Path


def main():
    """Create the required directory structure for the project."""
    # Determine the project root based on the script location
    # Assuming this script is in code/, the root is the parent directory
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    # Define the required directories
    required_dirs = [
        "data/raw",
        "data/processed",
        "state",
        "code"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            if full_path.is_dir():
                print(f"Directory already exists: {full_path}")
                existing_count += 1
            else:
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    print(f"\nSetup complete. Created {created_count} new directories, {existing_count} already existed.")
    print(f"Project root: {project_root}")
    print("\nDirectory structure:")
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        print(f"  {full_path}")


if __name__ == "__main__":
    main()