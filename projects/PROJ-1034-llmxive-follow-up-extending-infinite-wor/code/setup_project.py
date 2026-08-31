import os
import sys
from typing import List

# Define the required directory structure relative to the project root
REQUIRED_DIRS: List[str] = [
    "src/sim",
    "src/analysis",
    "src/data",
    "src/cli",
    "src/tests",
    "data/raw",
    "data/processed",
    "docs",
    "state",
]

def create_directory(path: str) -> bool:
    """
    Create a directory if it does not exist.
    Returns True if successful, False otherwise.
    """
    try:
        os.makedirs(path, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def create_file(path: str, content: str = "") -> bool:
    """
    Create a file with optional content.
    Returns True if successful, False otherwise.
    """
    try:
        # Ensure parent directory exists
        parent_dir = os.path.dirname(path)
        if parent_dir and not os.path.exists(parent_dir):
            os.makedirs(parent_dir, exist_ok=True)

        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except OSError as e:
        print(f"Error creating file {path}: {e}", file=sys.stderr)
        return False

def main() -> int:
    """
    Main entry point to create the project structure.
    Returns 0 on success, 1 on failure.
    """
    success = True
    print("Creating project directory structure...")
    for dir_path in REQUIRED_DIRS:
        if create_directory(dir_path):
            print(f"  [OK] {dir_path}")
        else:
            success = False
            print(f"  [FAIL] {dir_path}")

    if success:
        print("Project structure creation completed successfully.")
        return 0
    else:
        print("Project structure creation failed with errors.")
        return 1

if __name__ == "__main__":
    sys.exit(main())