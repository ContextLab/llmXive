"""
Script to initialize the tests directory structure.
Creates the directory and a .gitkeep file to ensure version control tracking.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine project root based on the expected structure
    # The script is expected to be run from the project root or code directory
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir if current_dir.name == 'code' else current_dir.parent

    # Define the tests directory path relative to the code directory
    tests_dir = current_dir / 'tests'

    print(f"Initializing tests directory at: {tests_dir}")

    # Create the directory if it doesn't exist
    try:
        tests_dir.mkdir(parents=True, exist_ok=True)
        print(f"Directory created or already exists: {tests_dir}")
    except PermissionError:
        print(f"Error: Permission denied to create directory: {tests_dir}")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating directory: {e}")
        sys.exit(1)

    # Create .gitkeep file
    gitkeep_file = tests_dir / '.gitkeep'
    try:
        gitkeep_file.touch(exist_ok=True)
        print(f"Created .gitkeep file: {gitkeep_file}")
    except PermissionError:
        print(f"Error: Permission denied to create .gitkeep file: {gitkeep_file}")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating .gitkeep file: {e}")
        sys.exit(1)

    print("Tests directory initialization complete.")

if __name__ == '__main__':
    main()
