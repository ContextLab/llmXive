import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the required project directory structure if they do not exist.
    Verifies existence after creation.
    
    Directories created:
    - code/
    - data/raw/
    - data/processed/
    - data/reports/
    - tests/
    - state/
    
    Returns:
        bool: True if all directories were created or already existed successfully.
        Raises FileNotFoundError if verification fails.
    """
    # Define the project root relative to where this script is called or the current working directory
    # Since this script lives in 'code/', we go up one level to the project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "state"
    ]
    
    created_paths = []
    
    for dir_name in directories:
        full_path = project_root / dir_name
        
        if not full_path.exists():
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                created_paths.append(str(full_path))
                print(f"Created directory: {full_path}")
            except OSError as e:
                print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
                return False
        else:
            if not full_path.is_dir():
                print(f"Error: {full_path} exists but is not a directory.", file=sys.stderr)
                return False
            print(f"Directory already exists: {full_path}")
    
    # Verification step
    all_exist = True
    for dir_name in directories:
        full_path = project_root / dir_name
        if not full_path.exists() or not full_path.is_dir():
            print(f"Verification Failed: Directory {full_path} does not exist or is not a directory.", file=sys.stderr)
            all_exist = False
    
    if all_exist:
        print("\n✅ All required directories verified successfully.")
        return True
    else:
        print("\n❌ Verification failed. Some directories are missing.", file=sys.stderr)
        return False

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
