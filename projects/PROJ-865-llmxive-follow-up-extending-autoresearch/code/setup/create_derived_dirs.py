import os
import sys
from pathlib import Path

def create_directory_structure():
    """
    Creates the data/derived/ directory at the repository root.
    This directory is intended for intermediate and processed data artifacts.
    """
    # Determine the project root (assuming script is in code/setup/)
    current_dir = Path(__file__).resolve().parent
    project_root = current_dir.parent.parent
    
    target_dir = project_root / "data" / "derived"
    
    try:
        target_dir.mkdir(parents=True, exist_ok=True)
        print(f"Successfully created directory: {target_dir}")
        return True
    except OSError as e:
        print(f"Error creating directory {target_dir}: {e}", file=sys.stderr)
        return False

def main():
    """
    Entry point for creating the data/derived/ directory.
    """
    success = create_directory_structure()
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()