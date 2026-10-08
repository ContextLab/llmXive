"""
Task T008: Create directory structure for the project.

Creates the following directories relative to the project root:
- data/raw/
- data/processed/
- data/spot_check/
- artifacts/
- tests/

This script is idempotent; running it multiple times will not error if directories exist.
"""
import os
from pathlib import Path

def main():
    """Create the required directory structure."""
    # Determine project root based on the script location
    # The script is located at code/create_directories.py
    # Project root is the parent of 'code'
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "spot_check",
        project_root / "artifacts",
        project_root / "tests",
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Directory creation complete. {created_count} new directories created.")
    
    # Verify existence
    for dir_path in directories:
        assert dir_path.exists(), f"Failed to create directory: {dir_path}"
        assert dir_path.is_dir(), f"Path is not a directory: {dir_path}"
    
    print("All directories verified successfully.")

if __name__ == "__main__":
    main()