import os
import sys
from pathlib import Path


def create_directory_structure():
    """
    Creates the required directory structure for the llmXive project.
    Directories created:
        - code/
        - tests/
        - data/
        - data/raw/
        - data/processed/
        - data/results/
        - data/logs/
        - scripts/
    """
    # Define the base project root (assuming script is run from project root or code/)
    # We use the parent of this file's directory to ensure we are at project root
    current_file = Path(__file__)
    project_root = current_file.parent.parent

    directories = [
        project_root / "code",
        project_root / "tests",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
        project_root / "data" / "logs",
        project_root / "scripts",
    ]

    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")

    print(f"Directory setup complete. {created_count} new directories created.")
    return True


def main():
    """Entry point for script execution."""
    try:
        success = create_directory_structure()
        if success:
            print("Success: Directory structure verified.")
            sys.exit(0)
        else:
            print("Error: Directory structure creation failed.")
            sys.exit(1)
    except Exception as e:
        print(f"Fatal error during directory setup: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
