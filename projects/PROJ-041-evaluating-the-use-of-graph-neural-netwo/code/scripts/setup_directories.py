"""
Script to create the required project directory structure for llmXive.
This script ensures all necessary directories exist for data, code, tests, and results.
"""
import os
import sys

# Define the root directory (assumed to be the project root)
# We use the current working directory as the base
BASE_DIR = os.getcwd()

# List of directories to create relative to BASE_DIR
DIRECTORIES = [
    "code/data",
    "code/models",
    "code/analysis",
    "code/utils",
    "data/raw",
    "data/processed",
    "data/results",
    "tests",
    "tests/integration",
]

def ensure_dir(dir_path: str) -> bool:
    """
    Creates a directory if it does not exist.
    Returns True if successful, False otherwise.
    """
    full_path = os.path.join(BASE_DIR, dir_path)
    try:
        os.makedirs(full_path, exist_ok=True)
        print(f"Created/Verified: {full_path}")
        return True
    except OSError as e:
        print(f"Error creating {full_path}: {e}")
        return False

def main():
    """Main entry point to create all required directories."""
    print(f"Project Root: {BASE_DIR}")
    print("Creating required directory structure...")
    
    success = True
    for dir_path in DIRECTORIES:
        if not ensure_dir(dir_path):
            success = False
    
    if success:
        print("\nAll directories created successfully.")
        sys.exit(0)
    else:
        print("\nSome directories failed to create.")
        sys.exit(1)

if __name__ == "__main__":
    main()