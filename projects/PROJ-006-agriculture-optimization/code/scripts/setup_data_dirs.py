import os
import sys
from pathlib import Path

def ensure_dir(path: Path):
    """Create a directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main():
    """Setup the required directory structure for the project."""
    # Determine project root relative to this script's location
    # Assuming this script is in code/scripts/, root is two levels up
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent

    # Define required directories relative to project root
    required_dirs = [
        'data/raw',
        'data/processed',
        'data/logs',
        'state/projects'
    ]

    print(f"Setting up directories for project at: {project_root}")

    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        ensure_dir(dir_path)

    # Verify existence
    all_exist = True
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.is_dir():
            print(f"ERROR: Failed to create {dir_path}")
            all_exist = False

    if all_exist:
        print("All required directories created successfully.")
    else:
        print("Some directories failed to create.")
        sys.exit(1)

if __name__ == "__main__":
    main()