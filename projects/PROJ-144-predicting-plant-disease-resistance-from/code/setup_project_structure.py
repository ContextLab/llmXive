"""
Script to initialize the project directory structure for llmXive project PROJ-144.
Creates necessary folders for code, data (raw/processed), tests, and state.
"""
import os
import sys

def create_structure(root_dir: str) -> None:
    """
    Creates the standard project directory structure.
    
    Args:
        root_dir: The root directory of the project (usually current working dir).
    """
    directories = [
        "code",
        "code/utils",
        "code/data",
        "code/modeling",
        "data/raw",
        "data/processed",
        "data/figures",
        "tests/unit",
        "tests/integration",
        "state",
        "results",
        "specs",
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        full_path = os.path.join(root_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            if os.path.isdir(full_path):
                print(f"Directory already exists: {dir_path}")
                skipped_count += 1
            else:
                print(f"Warning: Path exists but is not a directory: {dir_path}")
                skipped_count += 1

    print(f"\nStructure initialization complete.")
    print(f"Created: {created_count}, Skipped/Exists: {skipped_count}")

if __name__ == "__main__":
    # Determine the project root (script is in code/, so go up one level)
    # However, to be safe, we run relative to the current working directory
    # which should be the project root when the script is executed.
    root = os.getcwd()
    print(f"Initializing structure in: {root}")
    create_structure(root)
