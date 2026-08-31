import os
import sys
from pathlib import Path

def create_directories() -> None:
    """
    Create the project directory structure as per the implementation plan.
    Creates directories for code modules, data storage, tests, and documentation.
    """
    base_path = Path.cwd()
    
    # Define all required directories relative to the project root
    directories = [
        "code/ingestion",
        "code/features",
        "code/modeling",
        "code/utils",
        "data/raw",
        "data/processed",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Directory creation complete. {created_count} new directories created.")

if __name__ == "__main__":
    create_directories()