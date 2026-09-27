"""
Task T004: Setup directory structure for the llmXive project.
Creates the required directory hierarchy under the project root.
"""
import os
import sys
from pathlib import Path

def setup_directories():
    """
    Creates the required directory structure:
    - data/raw
    - data/processed
    - data/interim
    - data/results
    - code/
    - tests/
    """
    # Determine project root (assuming this script is in code/ or root)
    # We look for the .git directory or a specific marker to find the root,
    # or default to the parent of this file if no marker is found.
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    # Define relative paths to create
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/interim",
        "data/results",
        "code",
        "tests"
    ]

    created_count = 0
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")

    print(f"Setup complete. Created {created_count} new directories.")
    return True

def main():
    """Entry point for the directory setup script."""
    try:
        success = setup_directories()
        if success:
            sys.exit(0)
        else:
            sys.exit(1)
    except Exception as e:
        print(f"Error during directory setup: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()