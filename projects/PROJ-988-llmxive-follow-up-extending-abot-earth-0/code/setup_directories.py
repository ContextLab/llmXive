"""
T001a: Create project directory structure for llmXive follow-up project.

This script initializes the required directory structure as per the project plan:
- code/
- data/ (with subdirs: raw/, processed/, results/, interim/)
- tests/
- docs/

All paths are relative to the project root.
"""
import os
import sys

def create_directory_structure(root_path: str) -> None:
    """
    Create the full directory structure for the llmXive project.
    
    Args:
        root_path: The root directory where the structure will be created.
    """
    # Define the directory structure
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "data/interim",
        "tests",
        "docs",
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        full_path = os.path.join(root_path, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            skipped_count += 1
            print(f"Exists (skipped): {full_path}")

    print(f"\nDirectory creation complete.")
    print(f"  Created: {created_count}")
    print(f"  Skipped (already exist): {skipped_count}")

def main():
    # Determine the project root (parent of the script's directory)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)

    print(f"Project root detected at: {project_root}")
    create_directory_structure(project_root)

if __name__ == "__main__":
    main()
