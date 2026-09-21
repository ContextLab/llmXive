import os
import sys
from pathlib import Path

def setup_directories():
    """
    Creates the required directory structure for the project:
    - data/raw/
    - data/processed/
    - data/models/
    - code/ (if not exists, though usually code files are already here)
    - tests/
    - specs/ (feature directory)
    - docs/
    - contracts/
    
    This script ensures the project skeleton exists before data ingestion or analysis begins.
    """
    # Define the project root relative to this script's location or current working directory
    # Since this file is in `code/`, we go up one level to the project root
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    directories = [
        "data/raw",
        "data/processed",
        "data/models",
        "code", # Ensure it exists
        "tests",
        "specs",
        "docs",
        "docs/reports",
        "contracts"
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
    
    print(f"Setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    setup_directories()
