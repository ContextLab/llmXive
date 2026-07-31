"""
Script to create the required project directory structure.
This script ensures all necessary folders exist for the pipeline.
"""
import os
from pathlib import Path

def create_directories():
    """Create the required directory structure for the project."""
    root = Path(".")
    
    # Define the required directories relative to the project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/features",
        "tests",
        "state/projects",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nDirectory setup complete. {created_count} new directories created.")
    return created_count

def main():
    """Entry point for the setup script."""
    create_directories()

if __name__ == "__main__":
    main()
