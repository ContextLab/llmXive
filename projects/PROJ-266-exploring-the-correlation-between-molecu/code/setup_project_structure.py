"""
Project Structure Initialization Script (T002).

This script creates the foundational directory structure required for the project:
- code/
- tests/
- data/

It executes the required os.makedirs calls and verifies the directories exist.
"""
import os
import sys
from pathlib import Path


def create_directories():
    """
    Create the core project directories: code/, tests/, data/.
    """
    # Define the directories to create relative to the project root
    dirs_to_create = ['code', 'tests', 'data']

    for dir_name in dirs_to_create:
        dir_path = Path(dir_name)
        # Execute the required makedirs call with exist_ok=True
        os.makedirs(str(dir_path), exist_ok=True)
        print(f"Created directory: {dir_path}")


def verify_directories():
    """
    Verify that the required directories were created successfully.
    """
    dirs_to_check = ['code', 'tests', 'data']
    all_exist = True

    for dir_name in dirs_to_check:
        dir_path = Path(dir_name)
        if not dir_path.is_dir():
            print(f"ERROR: Directory {dir_path} does not exist!")
            all_exist = False
        else:
            print(f"Verified directory: {dir_path}")

    return all_exist


def main():
    """
    Main entry point for the script.
    """
    print("Initializing project structure (Task T002)...")
    create_directories()
    
    if verify_directories():
        print("Project structure initialization successful.")
        sys.exit(0)
    else:
        print("Project structure initialization failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
