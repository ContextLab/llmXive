"""
Directory structure setup for the Molecular Topology Selectivity Project.
This script verifies and creates the required directory structure as per T001 and T004.
"""
import os
import sys
from pathlib import Path

def setup_directories():
    """
    Creates the project directory structure and verifies existence.
    Returns a list of created/verified paths.
    """
    project_root = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        "code",
        "code/utils",
        "data/raw",
        "data/processed",
        "data/models",
        "tests",
        "docs/reports",
        "contracts"
    ]
    
    created_or_verified = []
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_or_verified.append(str(full_path))
        print(f"Verified/Created: {full_path}")
    
    return created_or_verified

def main():
    """Entry point for directory setup."""
    print("Setting up project directory structure...")
    try:
        paths = setup_directories()
        print(f"\nSuccessfully verified/created {len(paths)} directories.")
        print("Structure verification complete.")
        return 0
    except Exception as e:
        print(f"ERROR: Failed to setup directories: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())