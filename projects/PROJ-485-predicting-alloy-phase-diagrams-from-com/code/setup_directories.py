import os
import sys

def create_directories():
    """
    Creates the project directory structure including the 'state/' directory.
    This script is intended to be run to initialize the project folders.
    """
    # Define all required directories relative to the project root
    # Assuming the script is run from the project root or the paths are relative to where it's executed
    # To be safe, we will use absolute paths based on the script's location if needed,
    # but standard practice is relative to current working directory (project root).
    
    # Core structure
    dirs = [
        "code",
        "code/ingest",
        "code/features",
        "code/models",
        "code/viz",
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "state"
    ]

    created_count = 0
    for dir_path in dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    if created_count > 0:
        print(f"Successfully created {created_count} directories.")
    else:
        print("All directories already exist.")

if __name__ == "__main__":
    create_directories()
