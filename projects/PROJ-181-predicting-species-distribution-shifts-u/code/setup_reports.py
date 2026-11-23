"""
Initialize project directory structure for Reports, Metrics, Logs, State, and Contracts.

This script creates the following directories under the project root:
- metrics/
- reports/
- logs/
- state/
- contracts/

It also verifies the creation of these directories and prints a summary.
"""
import os
import sys
from pathlib import Path
from config import PROJECT_ROOT

def main():
    """Create the required directories for reports, metrics, logs, state, and contracts."""
    # Define the directories to create relative to the project root
    # Note: The task description specifies paths relative to the project root,
    # but the existing code structure suggests using the PROJECT_ROOT from config.py
    # to determine the base path.
    
    # Based on T001a and T001b, the project root is:
    # projects/PROJ-181-predicting-species-distribution-shifts-u/
    # The config.py likely defines PROJECT_ROOT as this path or the repository root.
    # We will use PROJECT_ROOT as the base for all new directories.
    
    directories_to_create = [
        "metrics",
        "reports",
        "logs",
        "state",
        "contracts"
    ]
    
    created_count = 0
    failed_count = 0
    
    print(f"Creating directories under: {PROJECT_ROOT}")
    
    for dir_name in directories_to_create:
        dir_path = Path(PROJECT_ROOT) / dir_name
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                print(f"Created: {dir_path}")
                created_count += 1
            else:
                print(f"Already exists: {dir_path}")
                created_count += 1 # Count as success if it already exists
        except Exception as e:
            print(f"Failed to create {dir_path}: {e}")
            failed_count += 1
    
    print(f"\nDirectory creation summary:")
    print(f"  Successful: {created_count}")
    print(f"  Failed: {failed_count}")
    
    if failed_count > 0:
        sys.exit(1)
    
    # Verify all directories exist
    all_exist = True
    for dir_name in directories_to_create:
        dir_path = Path(PROJECT_ROOT) / dir_name
        if not dir_path.exists() or not dir_path.is_dir():
            print(f"Verification failed: {dir_path} does not exist or is not a directory.")
            all_exist = False
    
    if all_exist:
        print("All required directories verified successfully.")
        return 0
    else:
        print("Verification failed for one or more directories.")
        sys.exit(1)

if __name__ == "__main__":
    main()
