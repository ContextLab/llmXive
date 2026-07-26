"""
Setup script to create the required data directory structure.
Creates data/raw, data/processed, and data/artifacts directories.
"""
import os
from pathlib import Path
from utils.config import get_paths, ensure_directories

def main():
    """Create the data directory structure."""
    # Get base paths from config
    base_dir = get_paths()
    
    # Define the data subdirectories to create
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/artifacts"
    ]
    
    # Create directories
    for dir_path in data_dirs:
        full_path = base_dir / dir_path
        ensure_directories([full_path])
        print(f"Created directory: {full_path}")
    
    # Create a .gitkeep file in each directory to ensure they are tracked by git
    for dir_path in data_dirs:
        full_path = base_dir / dir_path
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {full_path}")

if __name__ == "__main__":
    main()