import os
import sys

def ensure_dir(path: str) -> bool:
    """
    Creates a directory at the given path if it does not exist.
    Returns True if the directory exists after the call (created or pre-existing).
    """
    try:
        os.makedirs(path, exist_ok=True)
        return os.path.isdir(path)
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point to create all required project directories.
    This script ensures the existence of the directory structure defined in Phase 1.
    """
    # Define all required directories relative to the project root
    # Note: T001i specifically targets tests/integration
    directories = [
        "code/data",
        "code/models",
        "code/analysis",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "tests/integration"  # Task T001i target
    ]

    all_success = True
    for dir_path in directories:
        if ensure_dir(dir_path):
            print(f"Verified: {dir_path}")
        else:
            print(f"FAILED: {dir_path}")
            all_success = False

    if not all_success:
        sys.exit(1)
    else:
        print("All directories verified successfully.")

if __name__ == "__main__":
    main()