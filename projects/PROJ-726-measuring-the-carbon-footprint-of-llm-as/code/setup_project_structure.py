import os
import sys
from pathlib import Path

def create_directory_structure(root_dir: str = ".") -> None:
    """
    Creates the required project directory structure.
    
    Args:
        root_dir: The root directory where the structure will be created.
    """
    base_path = Path(root_dir)
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/outputs",
        "tests",
        "tests/unit",
        "tests/contract",
        "specs",
        "config"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"\nProject structure setup complete. {created_count} new directories created.")

def main():
    """Entry point for the script."""
    create_directory_structure(".")

if __name__ == "__main__":
    main()