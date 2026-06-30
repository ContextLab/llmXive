"""
Script to initialize the project directory structure for PROJ-736.
This script creates all necessary directories as defined in task T001a.
"""

import os
from pathlib import Path

def create_directories():
    """Create the required directory structure."""
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define all required directories relative to the project root
    directories = [
        "code",
        "tests",
        "data",
        "docs",
        "data/raw",
        "data/processed",
        "data/results",
        "code/data",
        "code/modeling",
        "code/utils",
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
    
    print(f"\nSetup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    create_directories()
