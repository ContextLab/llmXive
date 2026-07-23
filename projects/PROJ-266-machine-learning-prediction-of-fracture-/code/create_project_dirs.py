"""
Script to create the required directory structure for the project.
This implements task T001a: Create code directories.
"""
import os
import sys

def main():
    # Define the base directory (project root)
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    # Define the directories to create relative to the project root
    # Task T001a: code directories
    code_dirs = [
        "code",
        "code/data",
        "code/models",
        "code/train",
        "code/explain"
    ]
    
    # Task T001b: data directories (creating them here to ensure structure exists for verification)
    data_dirs = [
        "data",
        "data/raw",
        "data/processed",
        "data/explainability"
    ]
    
    # Task T001c: test directories
    test_dirs = [
        "tests",
        "tests/unit",
        "tests/contract",
        "tests/integration"
    ]
    
    all_dirs = code_dirs + data_dirs + test_dirs
    created_count = 0
    
    for dir_path in all_dirs:
        full_path = os.path.join(base_dir, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Total directories created: {created_count}")
    
    # Verify existence
    print("\nVerification:")
    for dir_path in all_dirs:
        full_path = os.path.join(base_dir, dir_path)
        exists = os.path.isdir(full_path)
        print(f"  {dir_path}: {'EXISTS' if exists else 'MISSING'}")
        if not exists:
            sys.exit(1)
    
    print("\nAll required directories are present.")

if __name__ == "__main__":
    main()
