"""
Script to initialize the project directory structure for llmXive PROJ-182.
This script creates the necessary folders as defined in T001.
"""
import os
import sys

def main():
    # Define the root directory (current working directory or project root)
    # The task assumes we are running from the project root
    base_dirs = [
        "code/src/generators",
        "code/src/estimators",
        "code/src/metrics",
        "code/src/viz",
        "code/tests/unit",
        "code/tests/integration",
        "data",
        "results",
        "contracts",
        "config"
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in base_dirs:
        if not os.path.exists(dir_path):
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
            skipped_count += 1

    print(f"\nSetup complete. Created: {created_count}, Skipped: {skipped_count}")

    # Verify structure
    print("\nVerifying structure:")
    for dir_path in base_dirs:
        exists = os.path.isdir(dir_path)
        status = "✓" if exists else "✗"
        print(f"  {status} {dir_path}")

    if not all(os.path.isdir(d) for d in base_dirs):
        print("\nError: Some directories failed to create.")
        sys.exit(1)

if __name__ == "__main__":
    main()
