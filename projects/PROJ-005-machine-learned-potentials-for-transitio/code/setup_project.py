import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the standard project directory structure for llmXive.
    Creates: src/, tests/, data/, data/raw/, data/processed/, data/results/, specs/
    Returns True if all directories were created successfully.
    """
    # Define the project root relative to the script location
    # The script is in code/, so root is one level up
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    directories = [
        "src",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "specs"
    ]

    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Project structure setup complete. Created {created_count} new directories.")
    return True

def main():
    """Entry point for the script."""
    success = create_directories()
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()