import os
from pathlib import Path
from config import ensure_directories

def setup_directories():
    """
    Create the required project directory structure:
    - code/
    - data/raw/
    - data/processed/
    - tests/

    This function uses ensure_directories from config.py to create the directories.
    """
    # Define the directory structure to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "tests"
    ]

    # Use ensure_directories from config to create each directory
    for dir_path in directories:
        ensure_directories([dir_path])
        print(f"Created directory: {dir_path}")

    return True

if __name__ == "__main__":
    setup_directories()
