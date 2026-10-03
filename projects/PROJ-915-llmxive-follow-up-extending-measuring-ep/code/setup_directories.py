"""
Project directory setup module for llmXive.
Creates the required root project directories and subfolders.
"""
import os
import sys
from pathlib import Path

def setup_directories():
    """
    Create the root project directories and test directories.
    Directories: code/, data/raw, data/processed, data/interim, data/results, state/,
                 tests/unit, tests/integration, docs/
    """
    # Determine project root based on the current file location
    # The script is in code/, so project root is the parent
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent

    # Define the directories to create relative to project root
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/interim",
        "data/results",
        "state",
        "tests/unit",
        "tests/integration",
        "docs"
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

    print(f"\nSetup complete. {created_count} new directories created.")
    return project_root

def main():
    """Entry point for directory setup."""
    print("Starting project directory setup...")
    root = setup_directories()
    print(f"Project root identified at: {root}")

    # Verify structure by listing top-level items
    print("\nCurrent project structure (top level):")
    for item in sorted(root.iterdir()):
        if item.is_dir():
            print(f"  [DIR] {item.name}")
        else:
            print(f"  [FILE] {item.name}")

    return 0

if __name__ == "__main__":
    sys.exit(main())