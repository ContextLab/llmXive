import os
from pathlib import Path

def main():
    """
    Setup the data directory structure for the project.
    Creates the following directories under the project root:
    - data/raw/
    - data/derived/
    - data/processed/
    
    This script ensures that the necessary folder hierarchy exists
    before data ingestion and processing tasks begin.
    """
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent
    data_dir = base_dir / "data"
    
    # Define required subdirectories
    subdirs = [
        "raw",
        "derived",
        "processed"
    ]
    
    created_count = 0
    for subdir in subdirs:
        dir_path = data_dir / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Ensure the main data directory exists
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created base data directory: {data_dir}")
    
    print(f"Data structure setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    exit(main())