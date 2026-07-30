import os
import sys

def main():
    """
    Creates the required data directory structure for the project.
    
    Directories created:
    - data/
    - data/raw/
    - data/processed/
    - data/explainability/
    
    These directories are essential for storing raw input data,
    preprocessed datasets, and model explainability artifacts.
    """
    base_dir = "data"
    subdirs = ["raw", "processed", "explainability"]
    
    # Create base directory if it doesn't exist
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        print(f"Created directory: {base_dir}")
    
    # Create subdirectories
    for subdir in subdirs:
        dir_path = os.path.join(base_dir, subdir)
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    print("Data directory structure creation complete.")
    
    # Verify all directories exist
    all_exist = True
    for subdir in [base_dir] + subdirs:
        if not os.path.isdir(subdir):
            print(f"ERROR: Directory {subdir} was not created successfully!")
            all_exist = False
    
    if all_exist:
        print("Verification: All required directories exist.")
        return 0
    else:
        print("Verification: Some directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())