"""
Setup script for PROJ-799: Statistical Properties of Integer Partitions into Distinct Prime Summands.
Creates the required directory structure as specified in task T001a.
"""
import os
import sys

# Define the project root relative to this script's location
# The script is located at: code/setup_structure.py
# We need to create structure relative to the project root (parent of code/)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(script_dir)

# Define the required directories relative to project_root
required_dirs = [
    "code",
    "code/utils",
    "data/raw",
    "data/processed",
    "data/schemas",
    "tests",
    "tests/data",
    "docs",
    "state/projects",
]

def main():
    created_count = 0
    existing_count = 0

    print(f"Project Root: {project_root}")
    print("Creating directory structure...")

    for dir_path in required_dirs:
        full_path = os.path.join(project_root, dir_path)
        if os.path.exists(full_path):
            existing_count += 1
            print(f"  [EXISTS] {dir_path}")
        else:
            os.makedirs(full_path, exist_ok=True)
            created_count += 1
            print(f"  [CREATED] {dir_path}")

    print(f"\nSummary: {created_count} directories created, {existing_count} already existed.")

    # Verify the structure
    print("\nVerifying structure:")
    all_exist = True
    for dir_path in required_dirs:
        full_path = os.path.join(project_root, dir_path)
        if os.path.isdir(full_path):
            print(f"  [OK] {dir_path}")
        else:
            print(f"  [FAIL] {dir_path}")
            all_exist = False

    if all_exist:
        print("\n✅ Directory structure setup complete.")
        return 0
    else:
        print("\n❌ Some directories failed to create.")
        return 1

if __name__ == "__main__":
    sys.exit(main())