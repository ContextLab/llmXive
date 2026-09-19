"""
Initialize the project directory structure for the plant root architecture prediction pipeline.

This script creates the necessary directories as defined in task T001a:
- code/
- data/
- data/raw
- data/processed
- data/logs
- tests/
- artifacts/
- figures/
"""
import os
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the directory paths relative to the project root
    # We assume the script is run from the project root or we determine root dynamically
    # For robustness, we'll resolve relative to the script's location if needed, 
    # but typically these tasks run from the repo root.
    project_root = Path(__file__).resolve().parent.parent
    
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "tests",
        "artifacts",
        "figures"
    ]
    
    created_count = 0
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nInitialization complete. {created_count} new directories created.")
    
    # Verify all directories exist
    all_exist = all((project_root / d).exists() for d in directories)
    if all_exist:
        print("All required directories are present.")
        return 0
    else:
        print("ERROR: Some directories failed to create.")
        return 1

if __name__ == "__main__":
    exit(main())