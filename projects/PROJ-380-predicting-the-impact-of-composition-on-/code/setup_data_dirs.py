"""
Setup script for the BMG Shear Modulus prediction project data directories.

Creates the required directory structure under `data/`:
- data/raw/
- data/processed/
- data/artifacts/

This script ensures the foundational directory structure exists before
data ingestion or model training pipelines are executed.
"""
import os
from pathlib import Path

def main():
    """Create the standard data directory structure."""
    # Define the project root relative to this script's location
    # Assuming this script is in code/ and project root is parent of code/
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"
    
    # Define required subdirectories
    directories = [
        data_root / "raw",
        data_root / "processed",
        data_root / "artifacts",
    ]
    
    created_count = 0
    existing_count = 0
    
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {directory}")
            created_count += 1
        else:
            print(f"Directory already exists: {directory}")
            existing_count += 1
    
    print(f"\nSetup complete. Created {created_count} directories, {existing_count} already existed.")
    print(f"Data root: {data_root}")
    
    # Verify structure
    if data_root.exists():
        print("\nCurrent structure:")
        for item in sorted(data_root.iterdir()):
            print(f"  {item.name}/")
    else:
        print("ERROR: Data root directory was not created.")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())