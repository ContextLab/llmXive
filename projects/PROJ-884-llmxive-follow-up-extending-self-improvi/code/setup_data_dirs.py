"""
Setup script for T004: Data Directory Structure.

Creates the required directory structure for the llmXive project:
- data/raw/ for immutable puzzles
- data/processed/ for logs/results

This script is idempotent and safe to run multiple times.
"""
import os
import sys
from pathlib import Path
from typing import List

# Define the project root relative to this script's location
# Assuming this script is at code/setup_data_dirs.py
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Define the required directories relative to the project root
REQUIRED_DIRS: List[Path] = [
    PROJECT_ROOT / "data" / "raw",
    PROJECT_ROOT / "data" / "processed",
]

def setup_data_directories() -> bool:
    """
    Creates the required data directory structure.
    
    Returns:
        bool: True if all directories were created or already existed, False on failure.
    """
    created_count = 0
    failed = False

    for dir_path in REQUIRED_DIRS:
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"Created directory: {dir_path}")
                created_count += 1
            else:
                if dir_path.is_dir():
                    print(f"Directory already exists: {dir_path}")
                else:
                    print(f"ERROR: Path exists but is not a directory: {dir_path}")
                    failed = True
        except OSError as e:
            print(f"ERROR: Failed to create directory {dir_path}: {e}")
            failed = True

    if not failed and created_count > 0:
        print(f"Successfully created {created_count} new directory(s).")
    elif not failed:
        print("All required directories already exist.")
    
    return not failed

def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Target Directories: {[str(d) for d in REQUIRED_DIRS]}")
    
    success = setup_data_directories()
    
    if success:
        # Verify structure exists
        all_exist = all(d.exists() and d.is_dir() for d in REQUIRED_DIRS)
        if all_exist:
            print("Verification: All required directories are present and are directories.")
            return 0
        else:
            print("Verification: Some directories are missing or invalid after setup.")
            return 1
    else:
        print("Setup failed. Please check the errors above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())