"""
Helper module to create raw data directory.
"""
import os
import sys
from pathlib import Path

def create_raw_data_directory():
    """
    Create raw data subdirectory and .gitkeep.
    """
    project_root = Path.cwd()
    base_data = project_root / "data"
    raw_dir = base_data / "raw"
    
    raw_dir.mkdir(parents=True, exist_ok=True)
    
    gitkeep = raw_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.write_text("# Raw data storage\n")
    
    print(f"Created raw data directory: {raw_dir}")

def main():
    create_raw_data_directory()

if __name__ == "__main__":
    main()