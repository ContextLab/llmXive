"""
Helper module to create data directories specifically.
"""
import os
import sys
from pathlib import Path

def create_data_directories():
    """
    Create data subdirectories: raw, processed, synthetic.
    """
    project_root = Path.cwd()
    base_data = project_root / "data"
    
    subdirs = ["raw", "processed", "synthetic"]
    
    for subdir in subdirs:
        dir_path = base_data / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep
        gitkeep = dir_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.write_text("# Data storage\n")
        
        print(f"Created data directory: {dir_path}")

def main():
    create_data_directories()

if __name__ == "__main__":
    main()