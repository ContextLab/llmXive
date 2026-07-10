import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-247.
    This script executes the equivalent of:
    mkdir -p data/raw data/processed data/ground_truth data/logs code/utils tests/unit tests/contract docs/paper scripts
    """
    base_path = Path(".")
    
    # Define the required directories relative to the project root
    directories = [
        "data/raw",
        "data/processed",
        "data/ground_truth",
        "data/logs",
        "code/utils",
        "tests/unit",
        "tests/contract",
        "docs/paper",
        "scripts"
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
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
