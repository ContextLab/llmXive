import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure as defined in tasks.md T001.
    Ensures all required directories exist under the project root.
    """
    # Define the base directory (project root)
    # We assume this script is run from the project root or code/ directory.
    # We will resolve relative to the script's parent to be safe if run from code/,
    # but standard practice is running from root.
    script_path = Path(__file__).resolve()
    # If running from code/, go up one level; otherwise assume root.
    # The task implies we are at the root.
    base_dir = script_path.parent.parent if script_path.name == "setup_project.py" and script_path.parent.name == "code" else script_path.parent

    # If the script is directly in the root (unlikely based on API surface), use parent
    if not base_dir.exists():
        base_dir = script_path.parent

    # Ensure we are operating relative to the project root.
    # Based on API surface, this file is at code/setup_project.py.
    # So project root is code/..
    project_root = script_path.parent.parent

    directories = [
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "data/metadata",
        "tests/unit",
        "tests/integration",
        "docs"
    ]

    created_count = 0
    existing_count = 0

    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            existing_count += 1

    print(f"Project structure setup complete.")
    print(f"Directories created: {created_count}")
    print(f"Directories already existing: {existing_count}")

    # Verify creation by listing
    print("\nCurrent project structure (relevant dirs):")
    for dir_path in directories:
        full_path = project_root / dir_path
        if full_path.exists():
            print(f"  [OK] {full_path}")
        else:
            print(f"  [FAIL] {full_path} (Missing)")
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())