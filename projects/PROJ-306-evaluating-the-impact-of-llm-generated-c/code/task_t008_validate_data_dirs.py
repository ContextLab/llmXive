"""
Task T008: Create and validate the data/ directory structure.

This script ensures the existence of all required subdirectories under data/.
It is an explicit validation step, redundant with T001/T001b but kept for 
verification purposes as per the task description.

Required structure:
data/
  ├── benchmarks/
  │   ├── raw/
  │   └── processed/
  ├── generated/
  ├── coverage_reports/
  ├── processed/
  └── outputs/
"""
import os
import sys
from pathlib import Path

def create_directory(path: Path) -> bool:
    """Create a directory if it does not exist."""
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}")
        return False

def main():
    # Define the project root relative to this script's location or current working dir
    # Assuming standard project layout where this script is in code/
    project_root = Path(__file__).resolve().parent.parent
    data_root = project_root / "data"

    # Define the required directory structure relative to data_root
    required_dirs = [
        "benchmarks/raw",
        "benchmarks/processed",
        "generated",
        "coverage_reports",
        "processed",
        "outputs"
    ]

    print(f"Validating data directory structure at: {data_root}")
    
    all_success = True
    for rel_dir in required_dirs:
        target_path = data_root / rel_dir
        print(f"Checking/Creating: {target_path}")
        if not create_directory(target_path):
            all_success = False
            print(f"  -> FAILED")
        else:
            print(f"  -> OK")

    if all_success:
        print("\nValidation successful: All required directories exist.")
        return 0
    else:
        print("\nValidation failed: Some directories could not be created.")
        return 1

if __name__ == "__main__":
    sys.exit(main())