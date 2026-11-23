import os
from pathlib import Path

def main():
    """
    Create the data directory structure and an empty checksums file.
    
    This task implements T004:
    - Creates data/raw/
    - Creates data/processed/
    - Creates an empty data/checksums.txt
    """
    # Define the base directory for this project
    # Since this script runs from the project root, we assume 'data' is relative to cwd
    base_path = Path.cwd()
    data_dir = base_path / "data"
    
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"
    checksums_file = data_dir / "checksums.txt"
    
    # Create directories
    raw_dir.mkdir(parents=True, exist_ok=True)
    processed_dir.mkdir(parents=True, exist_ok=True)
    
    # Create empty checksums.txt if it doesn't exist
    if not checksums_file.exists():
        checksums_file.touch()
    
    print(f"Created directories: {raw_dir}, {processed_dir}")
    print(f"Created empty file: {checksums_file}")

if __name__ == "__main__":
    main()