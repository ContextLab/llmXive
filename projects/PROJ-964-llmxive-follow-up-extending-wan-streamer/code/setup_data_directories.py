import os
import sys
from pathlib import Path

def setup_data_directories():
    """
    Create the required data subdirectories:
    - data/raw/
    - data/processed/
    - data/models/
    
    Returns True if all directories were created or already exist.
    """
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"
    
    required_dirs = [
        data_root / "raw",
        data_root / "processed",
        data_root / "models",
    ]
    
    for dir_path in required_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        if not dir_path.is_dir():
            raise RuntimeError(f"Failed to create directory: {dir_path}")
    
    return True

def main():
    """Entry point for script execution."""
    try:
        setup_data_directories()
        print("Data directories created successfully.")
        # Verification step as per task requirements
        project_root = Path(__file__).resolve().parent.parent
        data_root = project_root / "data"
        
        dirs_to_check = [
            data_root / "raw",
            data_root / "processed",
            data_root / "models",
        ]
        
        all_exist = True
        for d in dirs_to_check:
            exists = d.is_dir()
            print(f"Checking {d}: {'EXISTS' if exists else 'MISSING'}")
            if not exists:
                all_exist = False
        
        assert all_exist, "One or more required directories are missing."
        print("Verification passed: All required data directories exist.")
        
    except Exception as e:
        print(f"Error during setup: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()
