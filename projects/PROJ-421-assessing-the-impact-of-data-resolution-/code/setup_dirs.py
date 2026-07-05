"""
Setup script to create the project directory structure for PROJ-421.
This script creates the necessary folders under the project root.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to the script location or current working directory
    # Assuming the script is run from the repository root or the project root
    # The task specifies paths relative to the project root:
    # projects/PROJ-421-assessing-the-impact-of-data-resolution-/...
    
    # We will create the structure relative to the current working directory
    # to ensure it works regardless of where the script is invoked from,
    # provided the user is in the correct root.
    
    base_dir = Path("projects/PROJ-421-assessing-the-impact-of-data-resolution-")
    
    directories = [
        base_dir / "code",
        base_dir / "data" / "raw",
        base_dir / "data" / "derived",
        base_dir / "data" / "results",
        base_dir / "tests",
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())