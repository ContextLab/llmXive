import os
import pathlib
from pathlib import Path

def main():
    """
    Creates the required data directory structure for the project:
    - data/raw/
    - data/processed/
    - data/cache/
    - data/checksums/
    
    Each directory is created with a .gitkeep file to ensure they are tracked
    by version control even when empty.
    """
    # Determine the project root relative to this script's location
    # Script is at: projects/PROJ-438-the-effect-of-personalized-feedback-timi/code/setup_data_dirs.py
    # Project root is: projects/PROJ-438-the-effect-of-personalized-feedback-timi/
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/cache",
        "data/checksums"
    ]
    
    for dir_path in data_dirs:
        full_path = project_root / dir_path
        
        # Create directory if it doesn't exist
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
        
        # Create .gitkeep file
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {full_path}")
        else:
            print(f".gitkeep already exists in: {full_path}")

if __name__ == "__main__":
    main()