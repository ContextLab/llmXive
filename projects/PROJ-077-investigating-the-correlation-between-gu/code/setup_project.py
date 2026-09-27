"""
Project Setup Script for PROJ-077-investigating-the-correlation-between-gu.

This script initializes the project directory structure as required by T001.
It creates the necessary directories for raw data, processed data, code, and tests.
"""
import os
from pathlib import Path
from config import ensure_directories

def main():
    """
    Initialize the project directory structure.
    
    Creates the following directories relative to the project root:
    - data/raw
    - data/processed
    - code
    - tests
    """
    # Define the required directories relative to the project root
    # The ensure_directories function from config handles the creation
    # based on INPUT_PATHS and other configuration.
    
    # Explicitly define the paths for T001
    base_path = Path(".")
    dirs_to_create = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "code",
        base_path / "tests"
    ]
    
    print("Initializing project directory structure...")
    for dir_path in dirs_to_create:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    print("Project directory structure initialization complete.")

if __name__ == "__main__":
    main()