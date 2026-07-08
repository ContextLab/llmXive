"""
Script to create the project directory structure for PROJ-431.
This script ensures all required directories exist under the project root.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine project root (assuming script is in code/ directory)
    # If run as python code/setup_directories.py, root is parent of code/
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Define required directories relative to project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "results/models",
        "results/reports",
        "results/plots",
        "code",
        "tests"
    ]

    created_count = 0
    existing_count = 0

    print(f"Project root detected at: {project_root}")
    print("Creating directory structure...")

    for dir_path_str in required_dirs:
        dir_path = project_root / dir_path_str
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"  Created: {dir_path.relative_to(project_root)}")
                created_count += 1
            else:
                print(f"  Exists:  {dir_path.relative_to(project_root)}")
                existing_count += 1
        except OSError as e:
            print(f"  Error creating {dir_path.relative_to(project_root)}: {e}")
            sys.exit(1)

    print(f"\nDone. Created {created_count} directories, found {existing_count} existing.")

    # Verify the structure
    print("\nVerifying structure:")
    for dir_path_str in required_dirs:
        dir_path = project_root / dir_path_str
        if dir_path.exists() and dir_path.is_dir():
            print(f"  [OK] {dir_path.relative_to(project_root)}")
        else:
            print(f"  [FAIL] {dir_path.relative_to(project_root)}")
            sys.exit(1)

    print("\nAll required directories are present.")

if __name__ == "__main__":
    main()
