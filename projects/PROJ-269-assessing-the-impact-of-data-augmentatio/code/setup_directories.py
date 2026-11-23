import os
from pathlib import Path

def main():
    """
    Create project directory structure.
    
    Creates the following directories at the repository root:
    - data/raw/
    - data/derived/
    - results/
    - contracts/
    
    Also ensures code/ and tests/ exist (though T001a should have handled this).
    """
    # Define the base project root (current working directory or parent of code/)
    # Assuming this script runs from the project root
    base_path = Path.cwd()
    
    # Directories to create as per T001b
    directories = [
        "data/raw",
        "data/derived",
        "results",
        "contracts"
    ]
    
    # Also ensure code/ and tests/ exist (T001a)
    additional_dirs = [
        "code",
        "tests"
    ]
    
    all_dirs = directories + additional_dirs
    
    created_count = 0
    existing_count = 0
    
    for dir_name in all_dirs:
        dir_path = base_path / dir_name
        if dir_path.exists():
            existing_count += 1
            print(f"[INFO] Directory already exists: {dir_path}")
        else:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"[INFO] Created directory: {dir_path}")
    
    print(f"[INFO] Directory setup complete. Created: {created_count}, Existing: {existing_count}")
    return 0

if __name__ == "__main__":
    exit(main())
