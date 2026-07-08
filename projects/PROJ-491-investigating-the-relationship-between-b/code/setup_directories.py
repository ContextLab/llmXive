"""
Setup script for llmXive project structure.
Creates required directories for code, tests, data, and state management.
"""
import os
import sys

# Define the project root relative to this script's location or current working dir
# Assuming this script runs from the project root or code/ subdirectory
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Directories to create relative to project root
DIRECTORIES = [
    "code",
    "tests",
    "data/raw",
    "data/processed",
    "state"
]

def create_directories():
    """Create the required directory structure."""
    created = []
    failed = []
    
    for dir_path in DIRECTORIES:
        full_path = os.path.join(BASE_DIR, dir_path)
        try:
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
                created.append(dir_path)
                print(f"Created directory: {dir_path}")
            else:
                print(f"Directory already exists: {dir_path}")
        except OSError as e:
            failed.append((dir_path, str(e)))
            print(f"Error creating directory {dir_path}: {e}")
    
    if failed:
        print(f"\nFailed to create {len(failed)} directories:")
        for path, err in failed:
            print(f"  - {path}: {err}")
        sys.exit(1)
    else:
        print(f"\nSuccessfully created {len(created)} directories.")

if __name__ == "__main__":
    create_directories()
