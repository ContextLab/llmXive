"""
Script to create the data/raw directory for raw downloaded data.
Task: T006a
"""
import os
import sys
from pathlib import Path

def create_raw_data_directory(project_root: Path) -> None:
    """
    Creates the data/raw directory if it does not exist.
    
    Args:
        project_root: The root directory of the project.
    """
    raw_data_dir = project_root / "data" / "raw"
    raw_data_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created directory: {raw_data_dir}")

def main():
    # Determine project root based on script location
    # Script is located at code/setup_raw_data_directory.py
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    create_raw_data_directory(project_root)
    print("T006a: Directory creation complete.")

if __name__ == "__main__":
    main()