"""
Script to initialize the project directory structure for PROJ-826.
Creates required directories for data, code, tests, and state management.
"""
import os
import sys

# Define the project root relative to the script location or current working directory
# The task specifies paths relative to the project root.
# We assume this script is run from the repository root or the project root.
# To be safe, we calculate the target path based on the task description.

PROJECT_ROOT = "projects/PROJ-826-llmxive-follow-up-extending-memlens-benc"

# Directories to create as per T001
directories = [
    "data/raw",
    "data/processed",
    "code",
    "tests/unit",
    "state/projects"
]

def main():
    created_count = 0
    skipped_count = 0

    print(f"Initializing project structure in: {PROJECT_ROOT}")

    for dir_path in directories:
        full_path = os.path.join(PROJECT_ROOT, dir_path)
        
        if os.path.exists(full_path):
            print(f"  [SKIP] Directory already exists: {full_path}")
            skipped_count += 1
        else:
            try:
                os.makedirs(full_path, exist_ok=True)
                print(f"  [CREATED] {full_path}")
                created_count += 1
            except OSError as e:
                print(f"  [ERROR] Failed to create {full_path}: {e}")
                sys.exit(1)

    print(f"\nSetup complete. Created: {created_count}, Skipped: {skipped_count}")

if __name__ == "__main__":
    main()