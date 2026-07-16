"""
Project Directory Structure Setup Script.

This script initializes the required directory structure for the
Neural Correlates of Simulated Social Exclusion project.

It creates the following directories relative to the project root:
- data/raw: For original, unprocessed data downloads
- data/processed: For cleaned and preprocessed data
- data/results: For final analysis outputs and reports
- src: For source code modules
- tests: For unit and integration tests

This script is idempotent and will not fail if directories already exist.
"""

import os
import sys
from pathlib import Path

def main():
    """Create the required project directory structure."""
    # Determine the project root (parent of the code/ directory)
    # Assuming this script is located at code/setup_directories.py
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    # Define the required directories relative to the project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
        "src",
        "tests"
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Project root identified at: {project_root}")
    print("Creating directory structure...")
    
    for dir_path_str in required_dirs:
        dir_path = project_root / dir_path_str
        
        if dir_path.exists():
            if dir_path.is_dir():
                print(f"  [OK] Already exists: {dir_path}")
                existing_count += 1
            else:
                print(f"  [ERROR] Path exists but is not a directory: {dir_path}")
                sys.exit(1)
        else:
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"  [CREATED] {dir_path}")
                created_count += 1
            except OSError as e:
                print(f"  [ERROR] Failed to create {dir_path}: {e}")
                sys.exit(1)
    
    print(f"\nSetup complete: {created_count} directories created, {existing_count} already existed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())