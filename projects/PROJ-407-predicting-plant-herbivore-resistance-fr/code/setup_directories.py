"""
T006: Setup directory structure for the project.

Creates the required directory tree under the project root:
- code/
- data/raw/
- data/interim/
- data/processed/
- tests/
"""
import os
from pathlib import Path
import sys

def ensure_directories():
    """
    Create the standard project directory structure if it doesn't exist.
    
    Returns:
        bool: True if all directories were created or already exist.
    """
    # Define the root directory (project root)
    root = Path(__file__).resolve().parent.parent
    
    # Define relative paths to create
    directories = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data/results",
        "specs",
        "contracts"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
        elif not full_path.is_dir():
            # Should not happen in normal operation, but good to catch
            print(f"Warning: {full_path} exists but is not a directory")
    
    if created_count > 0:
        print(f"Created {created_count} new directories.")
    else:
        print("All required directories already exist.")
        
    return True

def main():
    """Entry point for script execution."""
    success = ensure_directories()
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()