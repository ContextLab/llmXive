import os
import sys
from pathlib import Path

def main():
    """
    Creates the root directory structure for the project.
    Directories created:
    - src/
    - tests/
    - data/
    - data/raw/
    - data/processed/
    - data/results/
    - docs/
    - contracts/
    - config/
    """
    # Determine the project root.
    # If this script is run from code/, we go up one level.
    # If run from root, we stay.
    script_path = Path(__file__).resolve()
    # Heuristic: if 'code' is in the path, assume we are inside the code folder
    # and need to go up to project root.
    if script_path.parent.name == 'code':
        project_root = script_path.parent
    else:
        # Fallback: assume current working directory is project root
        project_root = Path.cwd()

    # Define relative directories to create
    directories = [
        "src",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "docs",
        "contracts",
        "config"
    ]

    created_count = 0
    for dir_name in directories:
        target_path = project_root / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {target_path}")

    print(f"Setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())