import os
import sys
from pathlib import Path

def setup_data_directories():
    """
    Create the required data directory structure if it doesn't exist.
    
    Creates:
        data/raw
        data/processed
        data/results
    """
    base_dir = Path(__file__).resolve().parent.parent / "data"
    subdirs = ["raw", "processed", "results"]
    
    for subdir in subdirs:
        dir_path = base_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep to ensure directories are tracked by git
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
    
    print(f"Data directories created under {base_dir}")
