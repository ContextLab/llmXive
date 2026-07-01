import os
import sys
from pathlib import Path

def main():
    """
    Creates the required project directory structure.
    Executes the equivalent of: mkdir -p data/raw data/processed code tests docs
    """
    base_dir = Path(".")
    
    # Define the directories to create relative to the project root
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "docs"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
