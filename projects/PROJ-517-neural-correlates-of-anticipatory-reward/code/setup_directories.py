import os
from pathlib import Path

def main():
    """
    Creates the required project directories for the neural correlates project.
    Specifically creates the spec directory for the first feature.
    """
    # Define the project root (assumed to be the directory containing this script's parent)
    # We assume the script is run from the project root or the directory structure is relative to cwd
    project_root = Path.cwd()
    
    # Directories to create based on T001a, T001b, and T001c
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/figures",
        "specs/001-neural-correlates-of-anticipatory-reward"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())
