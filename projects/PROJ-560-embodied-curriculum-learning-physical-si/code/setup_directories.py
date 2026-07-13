import os
import sys
from pathlib import Path

def create_directory(path: str) -> None:
    """Create a directory if it does not exist."""
    try:
        Path(path).mkdir(parents=True, exist_ok=True)
        print(f"Directory created/exists: {path}")
    except OSError as e:
        print(f"Error creating directory {path}: {e}")
        sys.exit(1)

def main() -> None:
    """Setup the required directory structure for the project."""
    # Define relative paths based on project root (assumed to be parent of code/)
    # The task requires: data/raw, data/processed, data/synthetic, data/derivation_logs
    # We assume the script is run from the project root or code/ directory.
    # To be safe, we resolve relative to the script location's parent (project root)
    # or current working directory if run explicitly.
    
    # Let's assume the project root is the directory containing 'code/'
    # If run as `python code/setup_directories.py`, cwd might be code/.
    # We will create directories relative to the current working directory
    # but ensure they are under the project structure.
    
    # Based on T001, the structure is:
    # data/raw
    # data/processed
    # data/synthetic
    # data/derivation_logs
    
    # We will create these relative to the current working directory.
    # If the user runs this from the project root, it works.
    # If they run from code/, we might need to adjust, but standard practice
    # is to run setup scripts from the root.
    
    base_dirs = [
        "data/raw",
        "data/processed",
        "data/synthetic",
        "data/derivation_logs"
    ]
    
    print("Setting up directory structure...")
    for dir_path in base_dirs:
        create_directory(dir_path)
    
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()