"""
Setup script for project directory structure.
Creates the required directory tree for PROJ-227.
"""
import os
from pathlib import Path


def main():
    """Create the project directory structure."""
    # Project root relative to where this script is run (assumed project root)
    # The task specifies paths relative to the project root.
    # We assume the script is run from the project root or the parent of 'projects'.
    # To be safe, we define the base relative to the current working directory.
    
    project_name = "PROJ-227-assessing-the-trade-offs-between-static-"
    base_path = Path("projects") / project_name

    directories = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "state",
        base_path / "code",
        base_path / "tests",
        base_path / "tests" / "unit",
        base_path / "tests" / "integration",
        base_path / "tests" / "contract",
    ]

    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory exists: {directory}")

    if created_count == 0:
        print("All directories already exist.")
    else:
        print(f"Successfully created {created_count} directories.")

    # Verification: Print the tree structure
    print("\n--- Verification (ls -R style) ---")
    if base_path.exists():
        for root, dirs, files in os.walk(base_path):
            level = root.replace(str(base_path), '').count(os.sep)
            indent = ' ' * 2 * level
            print(f'{indent}{os.path.basename(root)}/')
            sub_indent = ' ' * 2 * (level + 1)
            for file in files:
                print(f'{sub_indent}{file}')
    else:
        print(f"Base path {base_path} does not exist after creation attempt.")


if __name__ == "__main__":
    main()