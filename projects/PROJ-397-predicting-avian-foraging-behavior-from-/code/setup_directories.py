"""
T001a: Create the project directory structure for PROJ-397.

This script creates the required folder hierarchy under the project root.
It ensures that the following directories exist:
code/data, code/models, code/viz, code/notebooks, code/utils, code/tests.
"""
import os
import sys

def main():
    # Define the project root relative to this script's location or current working directory
    # The task specifies paths relative to the project root.
    # We assume the script is run from the project root or the code directory.
    # To be safe, we construct the path relative to the current working directory.
    
    base_path = "code"
    sub_dirs = [
        "data",
        "models",
        "viz",
        "notebooks",
        "utils",
        "tests"
    ]

    created_dirs = []
    errors = []

    for subdir in sub_dirs:
        full_path = os.path.join(base_path, subdir)
        try:
            os.makedirs(full_path, exist_ok=True)
            created_dirs.append(full_path)
            print(f"Created/Verified: {full_path}")
        except Exception as e:
            errors.append(f"Failed to create {full_path}: {e}")

    if errors:
        print("Errors occurred during directory creation:")
        for err in errors:
            print(f"  - {err}")
        sys.exit(1)
    
    print(f"Successfully ensured {len(created_dirs)} directories exist.")

if __name__ == "__main__":
    main()
