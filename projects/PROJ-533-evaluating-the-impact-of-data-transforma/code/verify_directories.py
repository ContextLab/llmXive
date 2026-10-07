import os
import sys
from pathlib import Path

REQUIRED_DIRS = ["code", "data", "results", "tests"]

def verify_directory(dir_name: str) -> bool:
    """Verify that a directory exists relative to the project root."""
    project_root = Path(__file__).resolve().parent.parent
    dir_path = project_root / dir_name
    exists = dir_path.is_dir()
    return exists

def main():
    """Verify all required directories exist. Exit 1 if any are missing."""
    project_root = Path(__file__).resolve().parent.parent
    all_exist = True

    print(f"Checking directories from project root: {project_root}")
    for dir_name in REQUIRED_DIRS:
        dir_path = project_root / dir_name
        exists = dir_path.is_dir()
        status = "OK" if exists else "MISSING"
        print(f"  {dir_name}/: {status}")
        if not exists:
            all_exist = False

    if all_exist:
        print("All required directories verified.")
        sys.exit(0)
    else:
        print("ERROR: One or more required directories are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
