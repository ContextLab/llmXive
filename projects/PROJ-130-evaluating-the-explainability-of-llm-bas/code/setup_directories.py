import os
import sys
from pathlib import Path

# Define the project root based on the script location
# Assuming this script is run from the project root or code/ directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories to create for T003
DIRECTORIES_TO_CREATE = [
    "explanations",
    "state",
    "tests",
    # Ensure subdirectories for tests are ready for contract/integration tests
    "tests/contract",
    "tests/integration",
]

def ensure_directory(dir_path: Path) -> bool:
    """
    Creates a directory if it does not exist.
    Returns True if the directory was created or already existed.
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except PermissionError as e:
        print(f"Permission denied creating {dir_path}: {e}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error creating {dir_path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point to create required directories for T003.
    """
    print(f"Project Root: {PROJECT_ROOT}")
    print("Creating directories for T003...")

    success = True
    for dir_name in DIRECTORIES_TO_CREATE:
        full_path = PROJECT_ROOT / dir_name
        if ensure_directory(full_path):
            print(f"  [OK] Created/Verified: {full_path}")
        else:
            success = False
            print(f"  [FAIL] Failed to create: {full_path}")

    if success:
        print("All directories created successfully.")
        return 0
    else:
        print("Some directories failed to create.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
