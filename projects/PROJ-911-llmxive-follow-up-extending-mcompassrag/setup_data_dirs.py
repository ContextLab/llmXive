"""
Script to initialize the required directory structure for the project.
Creates data/raw, data/processed, and data/results directories.
"""
import os
from pathlib import Path
from code.config import DATA_DIR, PROJECT_ROOT, RAW_DIR, PROCESSED_DIR, RESULTS_DIR

def setup_directories():
    """
    Create all required data directories if they do not exist.
    """
    directories = [DATA_DIR, RAW_DIR, PROCESSED_DIR, RESULTS_DIR]
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Ensured directory exists: {dir_path}")
    
    print("Directory structure setup complete.")

if __name__ == "__main__":
    setup_directories()
