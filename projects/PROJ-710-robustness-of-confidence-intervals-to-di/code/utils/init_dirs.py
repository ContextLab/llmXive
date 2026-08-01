"""
Initialize project directory structure atomically.

Creates the required directory tree for the llmXive research pipeline:
- code/
- code/data/
- code/analysis/
- code/utils/
- code/tests/
- artifacts/

This script is idempotent and safe to run multiple times.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Define the project root relative to this script's location
# Assuming the script is at code/utils/init_dirs.py, root is 3 levels up
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent.parent

# Define required directories relative to project root
REQUIRED_DIRS: List[str] = [
    "code",
    "code/data",
    "code/analysis",
    "code/utils",
    "code/tests",
    "artifacts",
]

def create_directories() -> Tuple[int, int]:
    """
    Create all required directories if they do not exist.

    Returns:
        Tuple of (created_count, skipped_count)
    """
    created_count = 0
    skipped_count = 0

    for dir_path_str in REQUIRED_DIRS:
        dir_path = PROJECT_ROOT / dir_path_str
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                created_count += 1
                print(f"Created directory: {dir_path.relative_to(PROJECT_ROOT)}")
            else:
                skipped_count += 1
                # Silent skip for existing dirs to keep output clean unless verbose
                # print(f"Directory exists (skipped): {dir_path.relative_to(PROJECT_ROOT)}")
        except OSError as e:
            print(f"ERROR: Failed to create directory {dir_path}: {e}", file=sys.stderr)
            raise

    return created_count, skipped_count

def verify_directories() -> bool:
    """
    Verify that all required directories exist after creation.

    Returns:
        True if all exist, False otherwise.
    """
    all_exist = True
    for dir_path_str in REQUIRED_DIRS:
        dir_path = PROJECT_ROOT / dir_path_str
        if not dir_path.is_dir():
            print(f"VERIFICATION FAILED: Directory missing: {dir_path}", file=sys.stderr)
            all_exist = False
    return all_exist

def main() -> int:
    """
    Main entry point for the directory initialization script.

    Returns:
        Exit code: 0 for success, 1 for failure.
    """
    print(f"Project Root: {PROJECT_ROOT}")
    print(f"Initializing directory structure...")

    try:
        created, skipped = create_directories()
        print(f"Initialization complete: {created} created, {skipped} skipped.")

        if verify_directories():
            print("Verification successful: All required directories exist.")
            return 0
        else:
            print("Verification failed: Some directories are missing.", file=sys.stderr)
            return 1

    except Exception as e:
        print(f"Fatal error during initialization: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())