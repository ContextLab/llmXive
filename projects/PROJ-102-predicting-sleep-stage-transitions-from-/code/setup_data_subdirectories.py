import os
from pathlib import Path
import sys

def main():
    """
    Creates the required data subdirectories:
    - data/raw
    - data/processed
    - data/interim
    
    This script is idempotent and will not fail if directories already exist.
    """
    # Determine project root (assuming script is in code/ directory)
    # We traverse up from the script location to find the project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    data_dir = project_root / "data"
    
    # Ensure the main data directory exists
    data_dir.mkdir(parents=True, exist_ok=True)
    
    # Define required subdirectories
    subdirs = ["raw", "processed", "interim"]
    
    for subdir_name in subdirs:
        subdir_path = data_dir / subdir_name
        subdir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created/Verified: {subdir_path}")
    
    # Verify all directories exist
    all_created = all((data_dir / name).is_dir() for name in subdirs)
    
    if all_created:
        print("Success: All data subdirectories are ready.")
        return 0
    else:
        print("Error: Failed to create one or more data subdirectories.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())