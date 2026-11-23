import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in the implementation plan.
    Directories:
    - code/
    - data/raw/
    - data/processed/
    - data/analysis/
    - models/
    - analysis/
    - tests/
    - docs/
    """
    # Define the root directory (current working directory or project root)
    root = Path(".")
    
    # List of directories to create relative to root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/analysis",
        "models",
        "analysis",
        "tests",
        "docs"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nProject structure setup complete. {created_count} new directories created.")
    return created_count

def main():
    """Entry point for the script."""
    create_directories()

if __name__ == "__main__":
    main()
