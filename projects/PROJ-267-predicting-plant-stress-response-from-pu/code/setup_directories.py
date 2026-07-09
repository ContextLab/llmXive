"""
Script to create the project directory structure for the plant stress response pipeline.
Implements task T001a.
"""
import os
import sys

# Define the directory structure relative to the project root
# Based on the task description:
# code/data_ingestion, code/modeling, code/reporting, code/utils
# tests
# data/raw, data/processed
# results, logs, docs
directories = [
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

def main():
    project_root = os.getcwd()
    created_count = 0
    skipped_count = 0
    error_count = 0

    print(f"Creating project directory structure in: {project_root}")

    for dir_path in directories:
        full_path = os.path.join(project_root, dir_path)
        try:
            if os.path.exists(full_path):
                # Verify it's a directory, not a file
                if os.path.isdir(full_path):
                    skipped_count += 1
                    print(f"  [SKIP] {dir_path} (already exists)")
                else:
                    print(f"  [ERROR] {dir_path} exists but is not a directory")
                    error_count += 1
            else:
                os.makedirs(full_path, exist_ok=True)
                created_count += 1
                print(f"  [CREATED] {dir_path}")
        except OSError as e:
            print(f"  [ERROR] Failed to create {dir_path}: {e}")
            error_count += 1

    print("-" * 40)
    print(f"Summary: {created_count} created, {skipped_count} skipped, {error_count} errors")

    if error_count > 0:
        print("Some directories could not be created. Check errors above.")
        sys.exit(1)
    else:
        print("Directory structure setup complete.")
        sys.exit(0)

if __name__ == "__main__":
    main()
