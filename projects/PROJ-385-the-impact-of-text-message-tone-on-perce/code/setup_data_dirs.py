"""
Setup script to create the required data directory structure.
Creates: data/raw/, data/processed/, data/consent/
"""
import os
from pathlib import Path
from config import get_project_root, get_raw_data_dir, get_processed_data_dir, get_consent_dir

def create_directories():
    """Create the data directory structure required for the project."""
    project_root = get_project_root()
    data_root = project_root / "data"
    
    # Define required directories
    directories = [
        data_root,
        get_raw_data_dir(),
        get_processed_data_dir(),
        get_consent_dir()
    ]
    
    created = []
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            created.append(str(directory.relative_to(project_root)))
        else:
            # Ensure they are directories, not files
            if not directory.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {directory}")
    
    return created

def main():
    """Entry point for the script."""
    print("Creating data directory structure...")
    try:
        created = create_directories()
        if created:
            print(f"Created directories: {', '.join(created)}")
        else:
            print("All required directories already exist.")
        
        # Verification: List the created structure
        print("\nVerification of data directory structure:")
        data_root = get_project_root() / "data"
        for item in sorted(data_root.rglob("*")):
            if item.is_dir():
                print(f"  [DIR] {item.relative_to(get_project_root())}")
            else:
                print(f"  [FILE] {item.relative_to(get_project_root())}")
        
        return 0
    except Exception as e:
        print(f"Error creating directories: {e}")
        return 1

if __name__ == "__main__":
    exit(main())