import os
import sys
from pathlib import Path

def main():
    """
    Create the required project directories at the repository root:
    - src/
    - tests/
    - data/
    - state/

    This script ensures the directory structure exists for the pipeline.
    """
    # Determine the root directory (assuming this script is in code/ at root)
    # We need to go up one level from code/ to get to the root
    current_file = Path(__file__).resolve()
    root_dir = current_file.parent.parent

    directories = [
        root_dir / "src",
        root_dir / "tests",
        root_dir / "data",
        root_dir / "state"
    ]

    created = []
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path.relative_to(root_dir)))
        else:
            # Ensure it is a directory
            if not dir_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {dir_path}")
    
    if created:
        print(f"Created directories: {', '.join(created)}")
    else:
        print("All required directories already exist.")

    return 0

if __name__ == "__main__":
    sys.exit(main())