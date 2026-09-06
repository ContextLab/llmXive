import os
import sys
from typing import List

def create_directories() -> None:
    """
    Creates the required data directory structure for the OPID project.
    
    Directories created:
    - data/raw/synthetic_graphs/
    - data/processed/
    - data/figures/
    - data/logs/
    
    This function ensures that all necessary directories exist before
    any data generation or experiment execution begins.
    """
    base_dirs = [
        "data",
        "data/raw",
        "data/raw/synthetic_graphs",
        "data/processed",
        "data/figures",
        "data/logs",
    ]
    
    created_count = 0
    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            created_count += 1
        elif not os.path.isdir(dir_path):
            raise RuntimeError(f"Path exists but is not a directory: {dir_path}")
    
    print(f"Data directory setup complete. Created {created_count} new directories.")

def main() -> None:
    """Entry point for running the data directory setup script."""
    try:
        create_directories()
        print("SUCCESS: All required data directories are now in place.")
    except Exception as e:
        print(f"ERROR: Failed to create data directories: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
