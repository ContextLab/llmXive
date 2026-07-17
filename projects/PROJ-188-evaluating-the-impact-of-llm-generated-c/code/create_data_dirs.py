"""
Script to create the required data directory structure for the project.
Creates raw/, intermediate/, and processed/ subdirectories under data/.
"""
import os
from pathlib import Path

def create_data_directories():
    """Create the standard data directory structure."""
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"
    
    directories = [
        data_root / "raw",
        data_root / "intermediate",
        data_root / "processed"
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    if created_count == 0:
        print("All data directories already exist.")
    else:
        print(f"Successfully created {created_count} data directory/directories.")
    
    return data_root

if __name__ == "__main__":
    create_data_directories()