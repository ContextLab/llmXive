import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the standard project directories: code/, tests/, data/.
    This implements the requirement for T002.
    """
    # Ensure we are running from the project root or handle relative paths correctly
    # The script assumes it is run from the root where 'code', 'tests', 'data' should be created.
    # If run as a module, we need to resolve the path relative to the project root.
    
    # We use the current working directory as the base for directory creation
    # to ensure artifacts are written where the runner expects them.
    base_path = Path.cwd()
    
    directories = [
        base_path / 'code',
        base_path / 'tests',
        base_path / 'data'
    ]
    
    for dir_path in directories:
        os.makedirs(str(dir_path), exist_ok=True)
        print(f"Created/Verified directory: {dir_path}")

def verify_directories():
    """
    Verify that the required directories exist.
    """
    base_path = Path.cwd()
    directories = ['code', 'tests', 'data']
    
    all_exist = True
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.is_dir():
            print(f"ERROR: Directory missing: {dir_path}")
            all_exist = False
        else:
            print(f"Verified directory: {dir_path}")
    
    if not all_exist:
        raise FileNotFoundError("One or more required directories are missing.")

def main():
    logger = None
    try:
        create_directories()
        verify_directories()
        print("Project structure initialization successful.")
    except Exception as e:
        print(f"Failed to initialize project structure: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
