"""
Script to initialize the project directory structure for PROJ-239.

This script creates the necessary directories and empty __init__.py files
as specified in Task T001.
"""
import os
import sys

def main():
    # Define the relative paths to create based on T001 requirements
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/derived"
    ]

    # Create directories
    for dir_path in directories:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    # Create __init__.py files if they don't exist
    init_files = [
        "code/__init__.py",
        "tests/__init__.py"
    ]

    for file_path in init_files:
        if not os.path.exists(file_path):
            with open(file_path, "w") as f:
                f.write("# Package initialization\n")
            print(f"Created file: {file_path}")
        else:
            print(f"File already exists: {file_path}")

    # Verification step (simulating 'ls')
    print("\nVerification of project structure:")
    for dir_path in directories:
        if os.path.isdir(dir_path):
            print(f"  [OK] {dir_path}/")
        else:
            print(f"  [FAIL] {dir_path}/")
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())