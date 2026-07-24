import os
from pathlib import Path
from config import ensure_directories

def main():
    """
    Setup data directories for the project.
    Creates data/raw and data/processed directories with .gitkeep files.
    """
    ensure_directories()
    
    # Define the directories to create
    raw_dir = Path("data/raw")
    processed_dir = Path("data/processed")
    
    # Create directories if they don't exist
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Create .gitkeep files to ensure directories are tracked by git
    (raw_dir / ".gitkeep").touch()
    (processed_dir / ".gitkeep").touch()
    
    print(f"Created directory: {raw_dir}")
    print(f"Created directory: {processed_dir}")
    print(f"Created .gitkeep in: {raw_dir}")
    print(f"Created .gitkeep in: {processed_dir}")
