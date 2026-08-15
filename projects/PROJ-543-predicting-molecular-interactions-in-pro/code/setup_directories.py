"""
Setup script to create the required project directory structure.
Creates: code/, data/raw/, data/processed/, data/results/, tests/, specs/
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the project root (current directory)
    project_root = Path.cwd()
    
    # Define the directories to create relative to the project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "specs"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure setup complete. {created_count} new directory(ies) created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
