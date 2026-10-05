"""
T001: Initialize Project Structure
Creates the required directory structure for the llmXive automated science pipeline.
"""
import os
import sys
from pathlib import Path

def main():
    """
    Creates the following directories at the project root:
    - src/
    - tests/
    - data/raw
    - data/processed
    - data/results
    - logs/
    """
    # Determine project root (assuming this script is in code/ or code/code/)
    # We need to find the root where 'src', 'tests', 'data' should live.
    # Based on the API surface, the project root seems to be the parent of 'code' or 'code/code'.
    # Let's assume the script is run from the project root or the path is relative to it.
    # The task says "at repository root".
    
    # If running as `python code/setup_directories.py` from project root:
    # We need to create dirs relative to the current working directory.
    
    project_root = Path.cwd()
    
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/results",
        "logs"
    ]
    
    created = []
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    if not created:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {len(created)} directories.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
