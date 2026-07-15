"""
Script to create the required data directory structure.
Creates: data/, data/raw/, data/processed/, data/logs/
"""
import os
from pathlib import Path
from config import ensure_directories

def create_data_directories():
    """Create the data directory structure required by the project."""
    base_dir = Path("data")
    dirs_to_create = [
        base_dir,
        base_dir / "raw",
        base_dir / "processed",
        base_dir / "logs"
    ]
    
    ensure_directories(dirs_to_create)
    print(f"Created data directories under: {base_dir.absolute()}")
    return dirs_to_create

def main():
    """Entry point for the script."""
    create_data_directories()

if __name__ == "__main__":
    main()