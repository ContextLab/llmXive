"""
Script to create the data directory for the molecular toxicity project.
This script ensures the directory structure exists for storing datasets.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to the script location or standard project structure
    # Based on tasks.md, the data directory should be at:
    # projects/PROJ-356-predicting-molecular-toxicity-from-struc/code/data/
    
    # We assume the script is run from the project root or the code directory.
    # To be safe, we construct the path relative to the 'code' directory.
    script_path = Path(__file__).resolve()
    code_dir = script_path.parent
    
    # The data directory is a sibling to 'scripts', 'src', 'tests', etc.
    data_dir = code_dir / "data"
    
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created data directory: {data_dir}")
    else:
        print(f"Data directory already exists: {data_dir}")

    return 0

if __name__ == "__main__":
    exit(main())