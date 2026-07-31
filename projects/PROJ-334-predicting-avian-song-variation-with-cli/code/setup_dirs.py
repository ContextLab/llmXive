import os
import sys
from pathlib import Path

def main():
    """
    Create the required directory structure for the project.
    This script ensures that the following directories exist:
    - projects/PROJ-334-predicting-avian-song-variation-with-cli/
    - data/
    - code/
    - tests/
    
    It also creates subdirectories for data:
    - data/raw/
    - data/processed/
    """
    base_path = Path.cwd()
    
    # Define the required directories relative to the project root
    required_dirs = [
        base_path / "projects" / "PROJ-334-predicting-avian-song-variation-with-cli",
        base_path / "data",
        base_path / "code",
        base_path / "tests",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "figures",
        base_path / "specs",
        base_path / "contracts",
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path.relative_to(base_path)}")
            created_count += 1
        else:
            existing_count += 1
    
    print(f"Setup complete. Created {created_count} new directories, {existing_count} already existed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())