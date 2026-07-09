"""
Verify directory structure exists and is writable.
This script validates the project directory structure created by T001a.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the required directories relative to the project root
    # Based on T001a: mkdir -p code/data_ingestion code/modeling code/reporting code/utils tests data/raw data/processed results logs docs
    required_dirs = [
        "code/data_ingestion",
        "code/modeling",
        "code/reporting",
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "results",
        "logs",
        "docs"
    ]

    project_root = Path(__file__).resolve().parent.parent
    missing_dirs = []
    unwritable_dirs = []

    print(f"Verifying directory structure at: {project_root}")

    for dir_path in required_dirs:
        full_path = project_root / dir_path

        # Check existence
        if not full_path.exists():
            missing_dirs.append(dir_path)
            continue

        # Check if it is a directory
        if not full_path.is_dir():
            print(f"ERROR: {dir_path} exists but is not a directory.")
            missing_dirs.append(dir_path)
            continue

        # Check writability
        # We attempt to create a temporary file to verify write permissions
        test_file = full_path / ".write_test"
        try:
            if full_path.exists() and full_path.is_dir():
                # Check write permission
                if not os.access(full_path, os.W_OK):
                    unwritable_dirs.append(dir_path)
                else:
                    # Try to create a file
                    test_file.touch()
                    test_file.unlink()
        except (OSError, IOError) as e:
            print(f"ERROR: Cannot write to {dir_path}: {e}")
            unwritable_dirs.append(dir_path)

    # Report results
    if missing_dirs:
        print(f"FAILED: Missing directories: {', '.join(missing_dirs)}")
        sys.exit(1)

    if unwritable_dirs:
        print(f"FAILED: Unwritable directories: {', '.join(unwritable_dirs)}")
        sys.exit(1)

    print("SUCCESS: All required directories exist and are writable.")
    sys.exit(0)

if __name__ == "__main__":
    main()
