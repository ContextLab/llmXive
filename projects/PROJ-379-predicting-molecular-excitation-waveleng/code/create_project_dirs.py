import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-379-predicting-molecular-excitation-waveleng.
    
    Creates the following directories relative to the project root:
    - data/raw
    - data/processed
    - code
    - tests
    - docs
    
    This script is designed to be run from the project root:
    python code/create_project_dirs.py
    """
    # Define the project root. We assume this script runs from the project root.
    # If running from elsewhere, we can adjust, but standard practice is project root.
    project_root = Path.cwd()
    
    # Define the required directories relative to the project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "docs"
    ]
    
    created_count = 0
    
    for dir_path_str in required_dirs:
        dir_path = project_root / dir_path_str
        
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            # Verify it's actually a directory
            if dir_path.is_dir():
                print(f"Directory already exists: {dir_path}")
            else:
                print(f"Error: Path exists but is not a directory: {dir_path}")
                sys.exit(1)
    
    print(f"Project directory structure ready. Created {created_count} new directories.")
    
    # Verify the structure by listing what we expect
    print("\nVerifying directory structure:")
    for dir_path_str in required_dirs:
        dir_path = project_root / dir_path_str
        if dir_path.exists() and dir_path.is_dir():
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [FAIL] {dir_path}")
            sys.exit(1)

if __name__ == "__main__":
    main()
