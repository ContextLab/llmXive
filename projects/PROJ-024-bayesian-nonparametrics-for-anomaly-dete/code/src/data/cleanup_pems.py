"""
Task T054: Delete all PEMS-SF files from data/raw/

This script removes deprecated PEMS-SF datasets to ensure compliance
with the project's data hygiene requirements (only UCI datasets allowed).
"""
import os
import sys
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent.parent.parent
    data_raw_dir = project_root / "data" / "raw"
    
    if not data_raw_dir.exists():
        print(f"Directory {data_raw_dir} does not exist. Nothing to clean.")
        return 0
    
    pems_files = [
        "pems_sf.csv",
        "pems_sf_synthetic.csv"
    ]
    
    deleted_count = 0
    missing_files = []
    
    for filename in pems_files:
        file_path = data_raw_dir / filename
        if file_path.exists():
            try:
                file_path.unlink()
                print(f"Deleted: {file_path}")
                deleted_count += 1
            except PermissionError:
                print(f"ERROR: Permission denied deleting {file_path}")
                return 1
            except Exception as e:
                print(f"ERROR: Failed to delete {file_path}: {e}")
                return 1
        else:
            missing_files.append(filename)
    
    # Verify deletion
    remaining = []
    for filename in pems_files:
        if (data_raw_dir / filename).exists():
            remaining.append(filename)
    
    if remaining:
        print(f"WARNING: The following files still exist: {remaining}")
        return 1
    
    print(f"Cleanup complete. Deleted {deleted_count} PEMS-SF file(s).")
    if missing_files:
        print(f"Note: The following files were not found (already removed?): {missing_files}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())