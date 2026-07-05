import os
import sys
from pathlib import Path

def main():
    """
    Create root directories required for the project structure.
    Implements T001a: Create root directories: code/, data/, tests/, state/
    """
    # Define the root directory (project root)
    # We assume the script is run from the project root or we resolve relative to this file's parent
    root_dir = Path(__file__).resolve().parent.parent

    # Directories to create
    root_dirs = [
        "code",
        "data",
        "tests",
        "state"
    ]

    created = []
    skipped = []

    for dir_name in root_dirs:
        dir_path = root_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        else:
            skipped.append(str(dir_path))
            print(f"Directory already exists: {dir_path}")

    print(f"\nSummary: Created {len(created)} directories.")
    if skipped:
        print(f"Skipped {len(skipped)} existing directories.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())