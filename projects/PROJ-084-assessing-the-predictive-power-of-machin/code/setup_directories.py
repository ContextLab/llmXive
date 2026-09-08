import os
from pathlib import Path

def main():
    """
    Create the required project directory structure.
    Implements task T001a: Create code/, data/raw/, data/processed/, data/results/, tests/
    """
    # Define the project root (current directory or parent if in a subdirectory)
    # Assuming this script is run from the project root
    root = Path.cwd()

    # Define relative paths to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests"
    ]

    created_count = 0
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    print(f"Directory setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())
