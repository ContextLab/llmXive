"""
Setup script to create the project directory structure.
This script creates the necessary folders for data ingestion, modeling,
reporting, utilities, tests, raw/processed data, results, logs, and docs.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure."""
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define the directory structure to create
    directories = [
        "code/data_ingestion",
        "code/modeling",
        "code/reporting",
        "code/utils",
        "tests",
        "data/raw",
        "data/processed",
        "results",
        "logs",
        "docs"
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Creating project directory structure in: {base_dir}")
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        
        if full_path.exists():
            if full_path.is_dir():
                print(f"  [SKIP] {dir_path} (already exists)")
                skipped_count += 1
            else:
                print(f"  [ERROR] {dir_path} exists but is not a directory")
                sys.exit(1)
        else:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  [CREATE] {dir_path}")
                created_count += 1
            except PermissionError:
                print(f"  [ERROR] Permission denied creating {dir_path}")
                sys.exit(1)
            except Exception as e:
                print(f"  [ERROR] Failed to create {dir_path}: {e}")
                sys.exit(1)
    
    print(f"\nDirectory creation complete.")
    print(f"  Created: {created_count}")
    print(f"  Skipped: {skipped_count}")
    
    # Verify all directories exist and are writable
    print("\nVerifying directory structure...")
    all_good = True
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists() or not full_path.is_dir():
            print(f"  [FAIL] {dir_path} does not exist or is not a directory")
            all_good = False
        else:
            # Check writability by trying to create a temporary file
            try:
                test_file = full_path / ".write_test"
                test_file.touch()
                test_file.unlink()
                print(f"  [OK] {dir_path} (writable)")
            except Exception as e:
                print(f"  [FAIL] {dir_path} (not writable: {e})")
                all_good = False
    
    if not all_good:
        print("\n[ERROR] Directory verification failed.")
        sys.exit(1)
    
    print("\n[SUCCESS] All directories created and verified.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
