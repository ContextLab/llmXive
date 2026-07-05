import os
from pathlib import Path
from setup_directories import create_directory

def main():
    """
    Creates the data/raw/ directory structure.
    """
    root = Path(__file__).resolve().parent.parent
    raw_dir = root / "data" / "raw"
    
    print(f"Creating directory: {raw_dir}")
    create_directory(raw_dir)
    print(f"Directory '{raw_dir}' created successfully.")

if __name__ == "__main__":
    main()
