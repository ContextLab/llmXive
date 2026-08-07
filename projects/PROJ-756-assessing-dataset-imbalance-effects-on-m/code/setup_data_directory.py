"""
Task T001b: Create the project data directory structure.

This script ensures the existence of the `data/` directory and its
required subdirectories for raw and processed data as defined in the project
structure plan.

It does not fetch data (that is handled by downloaders/ingestion) but
prepares the filesystem to receive it.
"""
import os
import sys
from pathlib import Path

# Project root is the parent of the `code` directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DIR = DATA_DIR / "raw"
PROCESSED_DIR = DATA_DIR / "processed"
SYNTHETIC_DIR = DATA_DIR / "synthetic"

def create_data_directories():
    """Create the data directory hierarchy if it does not exist."""
    directories = [DATA_DIR, RAW_DIR, PROCESSED_DIR, SYNTHETIC_DIR]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Data directory structure ready. New directories created: {created_count}")
    return True

def main():
    """Entry point for the script."""
    try:
        success = create_data_directories()
        if success:
            print("T001b: Data directory setup completed successfully.")
            return 0
        else:
            print("T001b: Data directory setup failed.")
            return 1
    except Exception as e:
        print(f"T001b: Error during data directory setup: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())