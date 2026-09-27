"""
Verification script to ensure the directory structure required by T001a exists.
This script can be run to validate the project setup.
"""
import os
from pathlib import Path

def verify_structure():
    """Check if all required directories exist."""
    project_root = Path("projects/PROJ-312-evaluating-the-impact-of-code-generation")
    
    if not project_root.exists():
        print(f"ERROR: Project root {project_root} does not exist.")
        return False

    required_dirs = [
        "code",
        "data",
        "tests",
        "contracts",
        "artifacts",
        "state",
        "data/raw",
        "data/processed",
        "data/spot_check",
    ]

    all_good = True
    for dir_name in required_dirs:
        full_path = project_root / dir_name
        if not full_path.exists():
            print(f"MISSING: {full_path}")
            all_good = False
        else:
            print(f"OK: {full_path}")

    return all_good

if __name__ == "__main__":
    success = verify_structure()
    if success:
        print("\nAll required directories are present.")
        exit(0)
    else:
        print("\nSome required directories are missing. Run create_directories.py first.")
        exit(1)