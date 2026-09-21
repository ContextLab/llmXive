"""
Script to create the required directory structure for the project.
Implements Task T008.
"""
import os
from pathlib import Path

def main():
    """Create the directory structure for the project."""
    # Define the base directory for this project
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define the required subdirectories relative to the project root
    # Note: The task asks for these relative to the project root
    directories = [
        "data/raw",
        "data/processed",
        "data/spot_check",
        "artifacts",
        "tests"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Directory creation complete. {created_count} new directories created.")

if __name__ == "__main__":
    main()
