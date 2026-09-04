"""
Setup script to create the tests directory hierarchy.
Creates tests/ with unit and integration subdirectories.
Verifies that directories exist and are writable.
"""
import os
import sys
import argparse
from pathlib import Path
from typing import List

# Define the project root relative to this script's location
# Assuming script is in code/, project root is parent of code/
PROJECT_ROOT = Path(__file__).resolve().parent.parent

TESTS_BASE = PROJECT_ROOT / "tests"
UNIT_DIR = TESTS_BASE / "unit"
INTEGRATION_DIR = TESTS_BASE / "integration"

def setup_tests_directories() -> bool:
    """
    Create the tests directory hierarchy and verify writability.
    
    Returns:
        bool: True if all directories created and verified successfully, False otherwise.
    """
    directories_to_create = [
        TESTS_BASE,
        UNIT_DIR,
        INTEGRATION_DIR
    ]

    created_dirs = []
    errors = []

    for dir_path in directories_to_create:
        try:
            # Create directory if it doesn't exist, including parents
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            print(f"Created directory: {dir_path}")
        except PermissionError:
            errors.append(f"Permission denied creating directory: {dir_path}")
        except OSError as e:
            errors.append(f"Error creating directory {dir_path}: {e}")

    if errors:
        for error in errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return False

    # Verify writability
    writable_errors = []
    for dir_path in [UNIT_DIR, INTEGRATION_DIR]:
        test_file = dir_path / ".write_test"
        try:
            # Try to create a test file
            with open(test_file, 'w') as f:
                f.write("writable")
            # Try to read it back
            with open(test_file, 'r') as f:
                content = f.read()
                if content != "writable":
                    writable_errors.append(f"Write verification failed for {dir_path}: content mismatch")
            # Clean up test file
            test_file.unlink()
            print(f"Verified writability: {dir_path}")
        except PermissionError:
            writable_errors.append(f"Directory {dir_path} is not writable (PermissionError)")
        except OSError as e:
            writable_errors.append(f"Write verification failed for {dir_path}: {e}")

    if writable_errors:
        for error in writable_errors:
            print(f"ERROR: {error}", file=sys.stderr)
        return False

    print("\nDirectory hierarchy setup successful:")
    print(f"  - {TESTS_BASE}")
    print(f"    - {UNIT_DIR.relative_to(TESTS_BASE)}")
    print(f"    - {INTEGRATION_DIR.relative_to(TESTS_BASE)}")
    
    return True

def main():
    """Main entry point for the script."""
    parser = argparse.ArgumentParser(
        description="Setup tests directory hierarchy for llmXive project."
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Force recreation of directories even if they exist."
    )
    
    args = parser.parse_args()

    if args.force and TESTS_BASE.exists():
        print(f"Force flag set. Removing existing {TESTS_BASE}...")
        import shutil
        shutil.rmtree(TESTS_BASE)
        print(f"Removed {TESTS_BASE}.")

    success = setup_tests_directories()
    
    if not success:
        print("\nSetup failed. Please check error messages above.", file=sys.stderr)
        sys.exit(1)
    
    print("\nAll tests directories are ready.")
    sys.exit(0)

if __name__ == "__main__":
    main()
