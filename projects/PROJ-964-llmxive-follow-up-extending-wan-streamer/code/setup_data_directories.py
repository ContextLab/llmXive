import os
import sys
from pathlib import Path

def setup_data_directories():
    """
    Create the required data subdirectories:
    - data/raw/
    - data/processed/
    - data/models/
    
    Returns:
        tuple: (success: bool, created_paths: list)
    """
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"
    
    required_dirs = [
        "raw",
        "processed",
        "models"
    ]
    
    created_paths = []
    
    for dir_name in required_dirs:
        dir_path = data_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(dir_path))
        else:
            created_paths.append(str(dir_path))
    
    return True, created_paths

def verify_data_directories():
    """
    Verify that the required data subdirectories exist.
    
    Returns:
        tuple: (all_exist: bool, missing_dirs: list, existing_dirs: list)
    """
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"
    
    required_dirs = [
        "raw",
        "processed",
        "models"
    ]
    
    existing_dirs = []
    missing_dirs = []
    
    for dir_name in required_dirs:
        dir_path = data_root / dir_name
        if os.path.isdir(dir_path):
            existing_dirs.append(str(dir_path))
        else:
            missing_dirs.append(str(dir_path))
    
    all_exist = len(missing_dirs) == 0
    return all_exist, missing_dirs, existing_dirs

def main():
    """
    Main entry point to create and verify data directories.
    """
    print("Setting up data directories...")
    success, created = setup_data_directories()
    
    if success:
        print(f"Successfully created/verified directories:")
        for path in created:
            print(f"  - {path}")
    else:
        print("Failed to create data directories.")
        sys.exit(1)
    
    print("\nVerifying data directories...")
    all_exist, missing, existing = verify_data_directories()
    
    if all_exist:
        print("All required data directories exist.")
        for path in existing:
            print(f"  ✓ {path}")
        return 0
    else:
        print("ERROR: Some required data directories are missing:")
        for path in missing:
            print(f"  ✗ {path}")
        sys.exit(1)

if __name__ == "__main__":
    sys.exit(main())