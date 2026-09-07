import os
import sys
from pathlib import Path

def create_directories(base_path: str = None):
    """
    Creates the required project directory structure.
    Paths are relative to the project root.
    """
    if base_path is None:
        base_path = Path.cwd()
    else:
        base_path = Path(base_path)

    # Define the required directories based on tasks.md T001
    # Using 'code/' prefix as per project constraints and existing API surface
    dirs_to_create = [
        "src",
        "data/raw",
        "data/derived",
        "data/annotations",
        "results",
        "tests",
        "specs"
    ]

    created_count = 0
    for dir_name in dirs_to_create:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    return created_count

def main():
    """
    Entry point for the setup script.
    """
    print("Starting project directory setup...")
    created = create_directories()
    print(f"Setup complete. Created {created} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
