"""
Setup script to create the required directory structure for the project.
Creates data/raw, data/processed, data/synthetic, and data/derivation_logs.
"""
import os
import sys

# Base project root relative to this script location
# Assuming script is at code/setup_directories.py
# Project root is one level up
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_ROOT = os.path.join(PROJECT_ROOT, "data")

REQUIRED_DIRS = [
    "raw",
    "processed",
    "synthetic",
    "derivation_logs"
]

def create_directory(dir_name: str) -> bool:
    """
    Create a directory if it does not exist.
    Returns True if successful, False otherwise.
    """
    full_path = os.path.join(DATA_ROOT, dir_name)
    try:
        os.makedirs(full_path, exist_ok=True)
        print(f"Created directory: {full_path}")
        return True
    except OSError as e:
        print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point to create all required data directories.
    """
    print(f"Setting up data directories in: {DATA_ROOT}")
    
    if not os.path.exists(DATA_ROOT):
        os.makedirs(DATA_ROOT, exist_ok=True)
        print(f"Created data root: {DATA_ROOT}")

    success = True
    for dir_name in REQUIRED_DIRS:
        if not create_directory(dir_name):
            success = False

    if success:
        print("Directory structure setup complete.")
    else:
        print("Some directories failed to create.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()