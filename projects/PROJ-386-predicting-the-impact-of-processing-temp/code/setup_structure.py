"""
Script to initialize the project directory structure for PROJ-386.
Creates the required directories as per plan.md and tasks.md specifications.
"""
import os
import sys

def main():
    # Define the base directory (project root)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define the required directory structure relative to the base
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "tests",
        "state"
    ]

    created_count = 0
    skipped_count = 0

    print(f"Initializing project structure in: {base_dir}")

    for dir_path in directories:
        full_path = os.path.join(base_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            # Check if it's actually a directory
            if os.path.isdir(full_path):
                skipped_count += 1
            else:
                print(f"Error: Path exists but is not a directory: {full_path}")
                sys.exit(1)

    print(f"Structure initialization complete. Created: {created_count}, Skipped (exists): {skipped_count}")

if __name__ == "__main__":
    main()