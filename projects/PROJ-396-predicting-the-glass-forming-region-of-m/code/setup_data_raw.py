import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """Create the data/raw directory for storing raw downloaded data."""
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    raw_dir = data_dir / "raw"
    
    if not data_dir.exists():
        print(f"Warning: Parent directory {data_dir} does not exist. Creating it first.")
        data_dir.mkdir(parents=True, exist_ok=True)
        
    create_directory(raw_dir)
    print(f"Successfully created directory: {raw_dir}")
