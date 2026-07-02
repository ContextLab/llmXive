"""
Project structure initialization for PROJ-528.
Creates the required directory hierarchy for the research pipeline.
"""
import os
import sys


def create_project_structure(root_dir: str = ".") -> bool:
    """
    Create the standard project directory structure.

    Creates:
      - code/
      - tests/
      - data/raw/
      - data/processed/
      - contracts/
      - docs/

    Args:
        root_dir: Base directory where structure will be created. Defaults to current dir.

    Returns:
        True if all directories were created successfully, False otherwise.
    """
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "contracts",
        "docs"
    ]

    success = True
    created_count = 0

    for dir_name in directories:
        full_path = os.path.join(root_dir, dir_name)
        try:
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
                print(f"Created directory: {full_path}")
                created_count += 1
            else:
                print(f"Directory already exists: {full_path}")
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}")
            success = False

    if success:
        print(f"Project structure initialization complete. Created {created_count} new directories.")
    else:
        print("Project structure initialization encountered errors.")

    return success


if __name__ == "__main__":
    # Execute from the project root
    root = os.getcwd()
    create_project_structure(root)
