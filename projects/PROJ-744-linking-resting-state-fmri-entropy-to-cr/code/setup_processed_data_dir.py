"""
Task T001c: Create directory: data/processed
"""
import os
import sys
from pathlib import Path

def create_directory(path_str: str) -> bool:
    """
    Create a directory if it does not exist.
    
    Args:
        path_str: Relative or absolute path to the directory.
        
    Returns:
        True if directory was created or already exists, False on failure.
    """
    path = Path(path_str)
    try:
        path.mkdir(parents=True, exist_ok=True)
        # Verify creation by checking existence
        if path.is_dir():
            print(f"Directory created/verified: {path}")
            return True
        else:
            print(f"Error: Directory creation failed or verification failed for {path}")
            return False
    except PermissionError:
        print(f"Error: Permission denied when creating directory: {path}")
        return False
    except Exception as e:
        print(f"Error: Unexpected error creating directory {path}: {e}")
        return False

def main():
    """
    Main entry point for T001c.
    Creates the data/processed directory.
    """
    # Define the target directory relative to the project root
    # Assuming the script is run from the project root or the path is relative to it
    project_root = Path.cwd()
    target_dir = project_root / "data" / "processed"
    
    print(f"Attempting to create directory: {target_dir}")
    
    success = create_directory(str(target_dir))
    
    if success:
        print("Task T001c completed successfully.")
        return 0
    else:
        print("Task T001c failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
