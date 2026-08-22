"""
Script to set up the required test directory structure.
Creates tests/{unit,integration} directories.
"""
import os
import sys
from pathlib import Path
import stat

PROJECT_ROOT = Path(__file__).resolve().parent.parent
TESTS_DIR = PROJECT_ROOT / "tests"

SUBDIRS = ["unit", "integration"]

def setup_tests_directories():
    """
    Create the required test directory structure.
    """
    directories = [TESTS_DIR] + [TESTS_DIR / subdir for subdir in SUBDIRS]
    
    for directory in directories:
        if not directory.exists():
            print(f"Creating directory: {directory}")
            directory.mkdir(parents=True, exist_ok=True)
        else:
            print(f"Directory already exists: {directory}")
        
        # Verify writability
        test_file = directory / ".write_test"
        try:
            test_file.touch()
            test_file.unlink()
            print(f"Verified writable: {directory}")
        except OSError as e:
            print(f"Error: Directory {directory} is not writable: {e}")
            sys.exit(1)
        
        # Create __init__.py
        init_file = directory / "__init__.py"
        if not init_file.exists():
            init_file.touch()

def main():
    """
    Main entry point.
    """
    setup_tests_directories()
    print("Test directory structure setup complete.")

if __name__ == "__main__":
    main()