"""
Setup script for PROJ-761: Assessing Reproducibility of Machine-Learned Reaction Yield Models.
Creates the required directory structure as specified in T001.
"""
import os
import sys

def main():
    # Define the relative paths to be created
    directories = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts/logs",
        "artifacts/plots",
        "artifacts/reports",
        "contracts"
    ]

    created_count = 0
    skipped_count = 0

    for dir_path in directories:
        if os.path.exists(dir_path):
            print(f"Skipped (exists): {dir_path}")
            skipped_count += 1
        else:
            os.makedirs(dir_path, exist_ok=True)
            print(f"Created: {dir_path}")
            created_count += 1

    print(f"\nSetup complete. Created {created_count} directories, skipped {skipped_count}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())