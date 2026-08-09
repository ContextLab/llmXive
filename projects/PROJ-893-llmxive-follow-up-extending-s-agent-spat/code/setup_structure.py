"""
Project Structure Initialization Script for llmXive Follow-up.

This script creates the required directory structure for the project
as specified in plan.md and tasks.md (Task T001).

Directories created:
- code/
- data/raw/
- data/derived/
- data/results/
- specs/
- tests/
"""
import os
import sys

# Define the directory structure relative to the project root
# The script assumes it is run from the project root or passed the root path
BASE_DIRS = [
    "code",
    "data/raw",
    "data/derived",
    "data/results",
    "specs",
    "tests",
]

def create_directories(base_path: str) -> None:
    """
    Creates the necessary directory structure.
    
    Args:
        base_path: The root directory where the structure should be created.
    """
    created_count = 0
    for dir_path in BASE_DIRS:
        full_path = os.path.join(base_path, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    if created_count > 0:
        print(f"\nSuccessfully created {created_count} new directory(ies).")
    else:
        print("\nNo new directories created. Structure already complete.")

if __name__ == "__main__":
    # Determine the project root. 
    # If run as `python code/setup_structure.py`, we need to go up one level.
    # If run from root, we use the current directory.
    # We default to the current working directory but allow override via argument.
    if len(sys.argv) > 1:
        root_path = sys.argv[1]
    else:
        # Default to current working directory
        root_path = os.getcwd()
    
    print(f"Initializing project structure in: {root_path}")
    create_directories(root_path)
