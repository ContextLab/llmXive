import os
from pathlib import Path

def main():
    """
    Main entry point to create the initial project directories.
    This script ensures the 'data' directory and its subdirectories exist.
    """
    # Determine project root relative to this script's location
    # Assuming script is in: projects/PROJ-298-.../code/setup_directories.py
    # We need to go up 2 levels to get to the project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    data_dir = project_root / "data"
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Create standard subdirectories
    subdirs = ["raw", "processed", "events", "taxonomy"]
    for subdir in subdirs:
        (data_dir / subdir).mkdir(parents=True, exist_ok=True)
        print(f"Created: {data_dir / subdir}")
    
    print(f"Data directory structure initialized at: {data_dir}")

if __name__ == "__main__":
    main()