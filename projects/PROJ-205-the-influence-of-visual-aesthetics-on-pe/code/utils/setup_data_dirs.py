"""
Utility script to initialize the project's data directory structure.
Creates `data/raw/` and `data/processed/` directories if they do not exist.
"""
import os
from pathlib import Path

def main():
    """
    Creates the required data directories relative to the project root.
    """
    # Determine project root (assuming this script is at code/utils/setup_data_dirs.py)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    data_dir = project_root / "data"
    
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    
    dirs_to_create = [raw_dir, processed_dir]
    
    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    if created_count == 0:
        print("All required data directories already exist.")
    else:
        print(f"Successfully created {created_count} new directory/directories.")

if __name__ == "__main__":
    main()