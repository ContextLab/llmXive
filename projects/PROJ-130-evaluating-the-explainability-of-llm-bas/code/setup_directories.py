import os
import sys
from pathlib import Path

# Define the project root relative to this file's location or current working directory
# Assuming this script runs from the project root or we calculate root from script location
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

# Directories to create
DIRECTORIES_TO_CREATE = [
    "explanations",
    "state",
    "tests",
]

def ensure_directory(dir_path: Path) -> bool:
    """
    Creates a directory if it does not exist.
    Returns True if successful, False otherwise.
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point to create required project directories.
    """
    print(f"Project root identified at: {PROJECT_ROOT}")
    created_count = 0
    failed_count = 0

    for dir_name in DIRECTORIES_TO_CREATE:
        target_path = PROJECT_ROOT / dir_name
        if ensure_directory(target_path):
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            failed_count += 1

    print(f"Directory creation summary: {created_count} created, {failed_count} failed.")

    if failed_count > 0:
        sys.exit(1)
    else:
        print("All required directories successfully created.")
        sys.exit(0)

if __name__ == "__main__":
    main()