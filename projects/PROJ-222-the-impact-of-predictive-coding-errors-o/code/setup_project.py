"""
Script to initialize the project directory structure for the llmXive project.
Creates necessary folders for data, code, figures, analysis, and contracts.
"""
import os
import sys

def create_directories():
    """Create the required project directory structure."""
    # Define the directories to create relative to the project root
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "figures",
        "analysis",
        "contracts"
    ]

    created = []
    failed = []

    for dir_path in directories:
        try:
            os.makedirs(dir_path, exist_ok=True)
            created.append(dir_path)
            print(f"Created directory: {dir_path}")
        except OSError as e:
            failed.append((dir_path, str(e)))
            print(f"Failed to create directory {dir_path}: {e}")

    if failed:
        print(f"\n{len(created)} directories created successfully.")
        print(f"{len(failed)} directories failed to create.")
        sys.exit(1)
    else:
        print(f"\nAll {len(created)} directories created successfully.")
        sys.exit(0)

if __name__ == "__main__":
    create_directories()