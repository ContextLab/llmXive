import os
import sys
from pathlib import Path
from config import ensure_directories

def main():
    """
    Initialize project directory structure.
    Creates: data/raw, data/processed, code, tests
    Verifies creation via exit code and log message.
    """
    # Ensure the base directories exist
    ensure_directories()
    
    # Define the required directories relative to the project root
    project_root = Path(__file__).resolve().parent.parent
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests"
    ]
    
    all_created = True
    for dir_path in required_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            if not dir_path.is_dir():
                all_created = False
                print(f"Error: Failed to create or verify directory: {dir_path}")
        except Exception as e:
            all_created = False
            print(f"Error creating directory {dir_path}: {e}")
    
    if all_created:
        print("Directories created successfully")
        return 0
    else:
        print("Failed to create some directories")
        return 1

if __name__ == "__main__":
    exit(main())
