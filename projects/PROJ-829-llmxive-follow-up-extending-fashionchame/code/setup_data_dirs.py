import os
import sys
from pathlib import Path

def main():
    """
    Creates the required directory structure for the llmXive project.
    Specifically creates data/raw and data/processed directories.
    """
    # Determine project root (assuming script is in code/ or code/setup/)
    # We assume the script is run from the project root or code/
    # To be safe, we resolve relative to the script location
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent if script_dir.name == 'code' else script_dir

    # Define directories to create
    directories = [
        project_root / 'data' / 'raw',
        project_root / 'data' / 'processed',
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")

    if created_count > 0:
        print(f"Successfully created {created_count} directory/directories.")
    else:
        print("No new directories were created; all exist already.")

    return 0

if __name__ == '__main__':
    sys.exit(main())