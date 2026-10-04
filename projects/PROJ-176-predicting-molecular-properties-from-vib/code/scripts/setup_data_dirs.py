"""
Script to initialize the project data directory structure.

Creates the following directories under the project root:
- data/raw/          : For original downloaded datasets (QM9, IR-spectra)
- data/preprocessed/ : For aligned and processed data (.npz files)
- data/external/     : For independent validation datasets
"""
import os
from pathlib import Path
import sys

# Ensure we are running from the project root or code directory
# Determine the project root relative to this script
script_dir = Path(__file__).resolve().parent
project_root = script_dir.parent.parent

data_root = project_root / "data"
directories = [
    data_root / "raw",
    data_root / "preprocessed",
    data_root / "external",
]

def main():
    print(f"Setting up data directories in: {data_root}")
    created_count = 0
    
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {directory}")
            created_count += 1
        else:
            print(f"  Exists:  {directory}")
    
    if created_count == 0:
        print("All data directories already exist.")
    else:
        print(f"Successfully created {created_count} directory/directories.")
    
    # Verify structure
    if data_root.exists() and all(d.exists() for d in directories):
        print("Data directory structure verification: PASSED")
        return 0
    else:
        print("Data directory structure verification: FAILED")
        return 1

if __name__ == "__main__":
    sys.exit(main())