"""
Script to create the required project directory structure.
This ensures all necessary folders exist before data processing begins.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to this script's location
    # Assuming script is at project_root/scripts/create_structure.py
    project_root = Path(__file__).parent.parent
    
    # Define the required directory structure
    directories = [
        "code",
        "code/src",
        "data",
        "data/raw",
        "data/processed",
        "tests",
        "tests/unit",
        "tests/integration"
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
    
    print(f"\nProject structure verification complete. Created {created_count} new directories.")
    print(f"Project root: {project_root}")

if __name__ == "__main__":
    main()