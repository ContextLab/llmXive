"""
Setup script to create the project directory structure.
Creates: src/, tests/, data/raw/, data/processed/, models/, templates/
"""
import os
import sys
from pathlib import Path

def main():
    """Create the required directory structure."""
    base_dir = Path(__file__).resolve().parent
    
    # Define directories to create
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "models",
        "templates"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nSetup complete. {created_count} new directory(ies) created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())