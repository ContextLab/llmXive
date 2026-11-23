import os
import sys
from pathlib import Path
import shutil

def setup_directories():
    """
    Creates the required directory structure for the project atomically.
    Creates: data/raw/, data/processed/, data/results/, state/
    
    Uses mkdir -p equivalent logic to ensure directories exist without error
    if they already exist.
    """
    # Determine project root (assuming code/src is two levels deep)
    # We need to go up two levels from code/src to reach project root
    project_root = Path(__file__).resolve().parent.parent.parent
    
    # Define required directories relative to project root
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "state"
    ]
    
    # Create directories atomically (mkdir -p behavior)
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {directory}")
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"Directory setup complete. Created {created_count} new directories.")
    
    # Verify all directories exist
    for directory in directories:
        if not directory.exists():
            raise RuntimeError(f"Failed to create required directory: {directory}")
        if not directory.is_dir():
            raise RuntimeError(f"Path exists but is not a directory: {directory}")
    
    return directories

if __name__ == "__main__":
    setup_directories()
