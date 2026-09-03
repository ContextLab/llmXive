"""
Script to create required project directories.
This script ensures the existence of all necessary folders for the llmXive pipeline.
"""
import os
import sys
from pathlib import Path

def create_directory(path_str: str) -> bool:
    """
    Create a directory if it does not exist.
    
    Args:
        path_str: The path to the directory to create.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    path = Path(path_str)
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main function to create all required directories for the project.
    """
    # Define all required directories relative to the project root (code/)
    required_dirs = [
        "scripts/",
        "data/raw/",
        "data/processed/",
        "data/splits/",
        "models/",
        "tests/",
        "logs/",
        "data/results/",
        "figures/"
    ]

    # Get the base directory (assuming this script is in code/scripts/)
    base_dir = Path(__file__).resolve().parent.parent
    
    print(f"Creating directories relative to: {base_dir}")
    
    all_success = True
    for dir_path in required_dirs:
        full_path = base_dir / dir_path
        if create_directory(str(full_path)):
            print(f"Created/Verified: {full_path}")
        else:
            print(f"Failed: {full_path}")
            all_success = False

    if all_success:
        print("\nAll required directories are ready.")
        return 0
    else:
        print("\nSome directories failed to create.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
