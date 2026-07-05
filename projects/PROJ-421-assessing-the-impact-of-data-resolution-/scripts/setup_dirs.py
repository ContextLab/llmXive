"""
Script to create the project directory structure for PROJ-421.
This script ensures all required folders exist on disk as per the task specification.
"""
import os
import sys

def main():
    # Define the base project root
    project_root = "projects/PROJ-421-assessing-the-impact-of-data-resolution-"
    
    # Define the required subdirectories relative to the project root
    required_dirs = [
        "code",
        "data/raw",
        "data/derived",
        "data/results",
        "tests"
    ]

    print(f"Ensuring directory structure for project: {project_root}")
    
    created_count = 0
    for dir_path in required_dirs:
        full_path = os.path.join(project_root, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path, exist_ok=True)
            print(f"  Created: {full_path}")
            created_count += 1
        else:
            print(f"  Exists:  {full_path}")
    
    print(f"Done. {created_count} new directories created.")
    
    # Verification: List the structure to confirm
    print("\nVerification of directory structure:")
    for dir_path in required_dirs:
        full_path = os.path.join(project_root, dir_path)
        if os.path.isdir(full_path):
            print(f"  [OK] {full_path}")
        else:
            print(f"  [FAIL] {full_path} does not exist!")
            return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())