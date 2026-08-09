import os
import sys
from pathlib import Path
from typing import List

# Project root relative to this file's location (code/)
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "PROJ-924-llmxive-follow-up-extending-agentdog-1-5"
PROJECT_PATH = PROJECT_ROOT / PROJECT_NAME

# Directories required by T001a
REQUIRED_DIRS: List[str] = [
    "code",
    "tests",
    "data/raw",
    "data/processed",
    "data/test",
    "specs",
    "docs",
    "specs/001-llmxive-drift-detection",
]

def ensure_directories() -> bool:
    """
    Create all required directories under the project root.
    Returns True if all directories were created or already exist.
    Raises FileNotFoundError if a directory creation fails.
    """
    all_good = True
    for dir_path_str in REQUIRED_DIRS:
        full_path = PROJECT_PATH / dir_path_str
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
        except Exception as e:
            print(f"ERROR: Failed to create directory {full_path}: {e}", file=sys.stderr)
            all_good = False
    return all_good

def main() -> int:
    """
    Entry point for the script.
    Returns 0 on success, 1 on failure.
    """
    print(f"Initializing project structure at: {PROJECT_PATH}")
    if PROJECT_PATH.exists():
        print(f"Project path already exists. Creating subdirectories.")
    else:
        print(f"Creating project root: {PROJECT_PATH}")
        PROJECT_PATH.mkdir(parents=True, exist_ok=True)

    if ensure_directories():
        print("SUCCESS: All required directories created/verified.")
        return 0
    else:
        print("FAILURE: Some directories could not be created.")
        return 1

if __name__ == "__main__":
    sys.exit(main())