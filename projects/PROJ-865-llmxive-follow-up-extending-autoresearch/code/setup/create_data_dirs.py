import os
import sys
from pathlib import Path

def create_directory_structure():
    """
    Creates the main data directories: raw, derived, artifacts.
    This wraps the logic for T001c, T001d, T001e.
    """
    # Determine the project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    data_root = project_root / "data"
    dirs_to_create = [
        data_root / "raw",
        data_root / "derived",
        data_root / "artifacts"
    ]

    success = True
    for target_dir in dirs_to_create:
        if target_dir.exists():
            print(f"Directory already exists: {target_dir}")
            continue

        try:
            target_dir.mkdir(parents=True, exist_ok=True)
            print(f"Successfully created directory: {target_dir}")
        except OSError as e:
            print(f"Error creating directory {target_dir}: {e}", file=sys.stderr)
            success = False

    return success

def main():
    success = create_directory_structure()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()