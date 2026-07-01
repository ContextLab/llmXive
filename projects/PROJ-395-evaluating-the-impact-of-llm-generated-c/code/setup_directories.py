"""
Setup script to create required project directories.
This script creates the data/raw, data/processed, state, and code directories
as required by task T004.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to this script's location
    # The script is in code/, so root is parent of code/
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    # Directories to create relative to project root
    directories = [
        "data/raw",
        "data/processed",
        "state",
        "code"
    ]

    created_count = 0
    existing_count = 0

    print(f"Project root: {project_root}")
    print("Setting up directories...")

    for dir_path in directories:
        full_path = project_root / dir_path
        
        if full_path.exists():
            print(f"[SKIP] {dir_path} already exists")
            existing_count += 1
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"[CREATE] {dir_path}")
            created_count += 1

    print(f"\nSetup complete: {created_count} created, {existing_count} existing")
    
    # Verify all directories exist
    all_exist = all((project_root / d).exists() for d in directories)
    if not all_exist:
        print("ERROR: Some directories were not created successfully")
        sys.exit(1)
    
    # List contents of project root for verification
    print("\nProject structure:")
    for item in sorted(project_root.iterdir()):
        if item.is_dir():
            print(f"  {item.name}/")
            for subitem in sorted(item.iterdir()):
                if subitem.is_dir():
                    print(f"    {subitem.name}/")

    return 0

if __name__ == "__main__":
    sys.exit(main())