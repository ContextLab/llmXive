import os
import sys
from pathlib import Path

def create_directory_structure():
    """
    Creates the data/raw/ directory at the repository root.
    This corresponds to task T001c.
    """
    # Determine the project root (parent of 'code' directory)
    # We assume this script runs from the project root or code/setup
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    target_dir = project_root / "data" / "raw"

    if target_dir.exists():
        print(f"Directory already exists: {target_dir}")
        return True

    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"Successfully created directory: {target_dir}")
        return True
    except OSError as e:
        print(f"Error creating directory {target_dir}: {e}", file=sys.stderr)
        return False

def main():
    success = create_directory_structure()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
