import os
import sys
from pathlib import Path

def create_data_directories():
    """
    Create the required directory structure for the project.
    Creates:
      - code/utils/
      - code/tests/
      - data/raw/
      - data/processed/
      - data/models/
    """
    base_path = Path(__file__).resolve().parent.parent
    
    directories = [
        base_path / "code" / "utils",
        base_path / "code" / "tests",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "models",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
    
    print(f"Total directories created: {created_count}")
    return created_count

def verify_data_directories():
    """
    Verify that all required directories exist.
    Returns True if all exist, False otherwise.
    """
    base_path = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        base_path / "code" / "utils",
        base_path / "code" / "tests",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "models",
    ]
    
    all_exist = True
    for directory in required_dirs:
        if not directory.exists():
            print(f"MISSING: {directory}")
            all_exist = False
        else:
            print(f"OK: {directory}")
    
    return all_exist

def main():
    """Main entry point for directory setup."""
    print("Starting directory creation...")
    create_data_directories()
    
    print("\nVerifying directories...")
    if verify_data_directories():
        print("\nAll required directories are present.")
        sys.exit(0)
    else:
        print("\nSome directories are missing!")
        sys.exit(1)

if __name__ == "__main__":
    main()
