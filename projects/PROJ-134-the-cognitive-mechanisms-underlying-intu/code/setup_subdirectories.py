import os
import sys
from pathlib import Path
from code.config import ensure_directories

def main():
    """
    Creates the required subdirectories for the project data and reports.
    
    This script implements task T001b by creating:
    - data/raw/
    - data/processed/
    - data/logs/
    - reports/
    
    It relies on code/config.py's ensure_directories function to perform the actual
    creation, ensuring consistency with the project's configuration management.
    """
    # Define the subdirectories relative to the project root
    # We assume the script is run from the project root or code/ directory
    # The config.py handles path resolution relative to the project root
    subdirs = [
        "data/raw",
        "data/processed",
        "data/logs",
        "reports"
    ]
    
    print(f"Creating subdirectories: {subdirs}")
    
    # Use the existing ensure_directories function from config
    # This function is already implemented in code/config.py
    ensure_directories(subdirs)
    
    print("Subdirectories created successfully.")
    
    # Verify creation (optional but good for confirmation)
    root = Path(__file__).resolve().parent.parent
    for subdir in subdirs:
        full_path = root / subdir
        if full_path.exists() and full_path.is_dir():
            print(f"  [OK] {full_path}")
        else:
            print(f"  [FAIL] {full_path} was not created")
            sys.exit(1)

if __name__ == "__main__":
    main()