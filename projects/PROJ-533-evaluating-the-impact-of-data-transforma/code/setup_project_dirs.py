import os
import sys
from pathlib import Path

REQUIRED_DIRS = ["code", "data", "results", "tests"]

def create_directory(dir_name: str) -> bool:
    """Create a directory if it does not exist."""
    project_root = Path(__file__).resolve().parent.parent
    dir_path = project_root / dir_name
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating {dir_name}/: {e}")
        return False

def verify_directory(dir_name: str) -> bool:
    """Verify that a directory exists relative to the project root."""
    project_root = Path(__file__).resolve().parent.parent
    dir_path = project_root / dir_name
    return dir_path.is_dir()

def main():
    """Create and verify all required directories."""
    project_root = Path(__file__).resolve().parent.parent
    print(f"Project root: {project_root}")

    # Create directories
    for d in REQUIRED_DIRS:
        if not verify_directory(d):
            print(f"Creating {d}/...")
            create_directory(d)
        else:
            print(f"{d}/ already exists.")

    # Verify
    all_good = True
    for d in REQUIRED_DIRS:
        if not verify_directory(d):
            print(f"FAILED: {d}/ does not exist after creation attempt.")
            all_good = False
        else:
            print(f"OK: {d}/ exists.")

    if all_good:
        print("All directories created and verified.")
        return 0
    else:
        print("ERROR: Directory creation/verification failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())