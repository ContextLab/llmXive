"""
Setup script to create the required data directory structure.

Creates the following subdirectories under `data/`:
- raw: For raw input data (synthetic or external)
- processed: For cleaned and engineered datasets
- split: For train/test/validation splits
"""
import os
from pathlib import Path

def main():
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"
    
    directories = [
        data_root / "raw",
        data_root / "processed",
        data_root / "split",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    print(f"Data directory structure ready at: {data_root}")

if __name__ == "__main__":
    main()