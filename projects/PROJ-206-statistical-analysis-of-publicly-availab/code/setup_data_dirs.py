import os
import sys
from pathlib import Path

def main():
    """
    Creates the required data directory structure at the project root.
    
    Creates:
        - data/
        - data/raw/
        - data/processed/
    
    Returns:
        bool: True if successful, False otherwise.
    """
    project_root = Path.cwd()
    data_dir = project_root / "data"
    raw_dir = data_dir / "raw"
    processed_dir = data_dir / "processed"

    dirs_to_create = [data_dir, raw_dir, processed_dir]

    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    # Verify creation
    if data_dir.exists() and raw_dir.exists() and processed_dir.exists():
        print("Data directory structure successfully created.")
        return True
    else:
        print("Failed to create data directory structure.")
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)