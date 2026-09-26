"""
Setup script to create the required directory structure for the llmXive project.
Ensures all necessary folders exist before data processing begins.
"""
import os
import sys
from typing import List

# Define the directory structure relative to the project root (code/../)
# The project root is assumed to be the parent of 'code'.
# However, since we are writing a script to be run, we will create dirs relative to the current working directory
# or explicitly relative to the script's location if needed.
# Based on task description: paths are relative to project root.
# The script itself lives in code/, so we need to go up one level or assume CWD is root.
# Standard practice: assume CWD is project root when running `python code/setup_data_dirs.py`

BASE_DIRS: List[str] = [
    "src",
    "src/environment",
    "src/agent",
    "src/simulation",
    "src/analysis",
    "tests",
    "data/raw/synthetic_graphs",
    "data/processed",
]

def create_directories(base_dirs: List[str] = BASE_DIRS) -> None:
    """
    Creates the specified directory structure if they do not already exist.
    
    Args:
        base_dirs: List of relative directory paths to create.
    """
    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

def main() -> None:
    """Entry point for the script."""
    print("Starting directory structure creation...")
    create_directories()
    print("Directory structure creation complete.")

if __name__ == "__main__":
    main()