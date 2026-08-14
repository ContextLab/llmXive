import os
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure for PROJ-397.
    
    Creates the following directories under code/:
    - data
    - models
    - viz
    - notebooks
    - utils
    - tests
    
    Also creates necessary subdirectories for data processing:
    - data/raw
    - data/processed
    - data/metadata
    """
    # Determine the project root relative to this script
    # The script is expected to be run from the project root or code/
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    
    # Define subdirectories to create
    subdirs = [
        "data",
        "data/raw",
        "data/processed",
        "models",
        "viz",
        "notebooks",
        "utils",
        "tests",
        "docs",
        "docs/results",
        "contracts"
    ]
    
    created_count = 0
    for subdir in subdirs:
        dir_path = code_dir / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nInitialization complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
