"""
Script to create the explicit directory tree for the project as per plan.md.
This satisfies task T001a.
"""
import os
import sys

# Define the root directory relative to the script location
# Assuming the script is at code/scripts/setup_directories.py
# The project root is code/../
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))

directories = [
    "src/models",
    "src/data",
    "src/training",
    "src/experiments",
    "src/utils",
    "tests/unit",
    "tests/integration",
    "scripts",
    "data/results",
    "data/logs",
    "data/configs",
    "state"
]

def main():
    created_count = 0
    for rel_dir in directories:
        full_path = os.path.join(project_root, rel_dir)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")

    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} directories.")

    # Verify structure
    print("\nVerifying project structure:")
    for rel_dir in directories:
        full_path = os.path.join(project_root, rel_dir)
        exists = os.path.isdir(full_path)
        status = "OK" if exists else "MISSING"
        print(f"  [{status}] {rel_dir}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
