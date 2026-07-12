import os
import sys
from pathlib import Path

def main():
    """
    Creates the required subdirectories for the project structure.
    Specifically creates:
    - src/data
    - src/features
    - src/models
    - src/utils
    
    Also ensures parent directories (src/, tests/, data/, specs/) exist
    as per T001a and T001b requirements, though T001a/b are marked done.
    """
    # Define the project root (assuming code/ is the root or we are running from project root)
    # The task implies we are working within the project tree.
    # We will assume the current working directory is the project root.
    project_root = Path.cwd()
    
    # Define the directories to create
    # Based on T001c: Create src/data, src/features, src/models, src/utils subdirectories
    directories_to_create = [
        "src/data",
        "src/features",
        "src/models",
        "src/utils"
    ]
    
    # Also ensure parent 'src' exists if not already
    # (Though T001a should have done this, we ensure robustness)
    created_dirs = []
    
    for dir_path in directories_to_create:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    if not created_dirs:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {len(created_dirs)} directories.")
        
    # Verify creation
    missing = []
    for dir_path in directories_to_create:
        if not (project_root / dir_path).exists():
            missing.append(dir_path)
    
    if missing:
        print(f"Error: The following directories could not be created: {missing}")
        sys.exit(1)
    else:
        print("Verification successful: All directories present.")

if __name__ == "__main__":
    main()