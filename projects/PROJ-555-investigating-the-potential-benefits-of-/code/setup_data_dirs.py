"""
Script to create the required data directory structure and .gitkeep files.

This task (T008) ensures the following directories exist:
- data/raw/landsat
- data/processed
- data/ecotourism

It also creates .gitkeep files in each to ensure the directories are tracked
by git even when empty.
"""
import os
from pathlib import Path
from config import ensure_directories

def main():
    # Define the directories relative to the project root
    # We assume the script is run from the project root or code/
    project_root = Path(__file__).resolve().parent.parent
    
    data_dirs = [
        project_root / "data" / "raw" / "landsat",
        project_root / "data" / "processed",
        project_root / "data" / "ecotourism",
    ]
    
    # Use the existing utility to ensure directories exist
    ensure_directories(data_dirs)
    
    # Create .gitkeep files
    for dir_path in data_dirs:
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in {gitkeep_path}")
        else:
            print(f".gitkeep already exists in {dir_path}")
    
    print("Data directory structure setup complete.")

if __name__ == "__main__":
    main()
