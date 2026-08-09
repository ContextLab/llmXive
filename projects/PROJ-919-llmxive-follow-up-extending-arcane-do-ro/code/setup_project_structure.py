import os
from pathlib import Path
import sys

def setup_directories():
    """
    Creates the required project directory structure for llmXive.
    Ensures all necessary folders exist for code, tests, data, and specs.
    """
    # Define project root relative to this script location or current working directory
    # Assuming the script is run from the project root or code/ directory
    root = Path(__file__).resolve().parent.parent
    
    # Define required directories
    directories = [
        "code/src",
        "code/tests",
        "code/data/raw",
        "code/data/derived",
        "code/data/gold_standard",
        "code/artifacts",
        "code/specs/001-gene-regulation",
        "code/specs/001-gene-regulation/contracts",
        "code/data/figures"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Project structure setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    setup_directories()
