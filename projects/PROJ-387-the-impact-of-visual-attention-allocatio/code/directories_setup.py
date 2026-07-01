"""
Script to create the base directory structure for the project.
This script is the entry point for T005.
"""
import sys
import os
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(project_root))

from utils.directories import create_base_directory_structure, verify_directory_structure
from utils.logger import setup_logging
from utils.config import set_global_seed

def main():
    # Set global seed for reproducibility
    set_global_seed()
    
    # Setup logging
    setup_logging()
    
    print("Creating base directory structure...")
    create_base_directory_structure()
    
    print("Verifying directory structure...")
    if verify_directory_structure():
        print("SUCCESS: All required directories created and verified.")
        return 0
    else:
        print("ERROR: Directory structure verification failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())