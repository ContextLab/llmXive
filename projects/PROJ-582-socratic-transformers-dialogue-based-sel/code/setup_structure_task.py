"""
T001 Implementation: Initialize project directory structure.

Creates the required directory tree and .gitkeep files for data directories.
"""
import os
import sys
from pathlib import Path

# Define the project root relative to this script's location or project root
# The task requires paths relative to the project root.
# We assume the script is run from the project root or the code directory.
# To be safe, we construct the absolute path based on the task requirements.
PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROJECT_NAME = "PROJ-582-socratic-transformers-dialogue-based-sel"
CODE_DIR = PROJECT_ROOT / PROJECT_NAME / "code"

# Define the required subdirectories
REQUIRED_DIRS = [
    "src",
    "data/raw",
    "data/processed",
    "data/results",
    "tests",
]

def create_directories():
    """Create all required directories."""
    print(f"Ensuring directories exist under: {CODE_DIR}")
    for dir_name in REQUIRED_DIRS:
        dir_path = CODE_DIR / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {dir_path}")
    return True

def create_gitkeep():
    """Create .gitkeep files in all data directories."""
    data_dirs = ["data/raw", "data/processed", "data/results"]
    for dir_name in data_dirs:
        dir_path = CODE_DIR / dir_name
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"  Created: {gitkeep_path}")
    return True

def verify_structure():
    """Verify that all required directories exist."""
    paths_to_check = [
        CODE_DIR / "src",
        CODE_DIR / "data/raw",
        CODE_DIR / "data/processed",
        CODE_DIR / "data/results",
        CODE_DIR / "tests",
    ]
    
    all_exist = True
    for p in paths_to_check:
        if not p.is_dir():
            print(f"MISSING: {p}")
            all_exist = False
        else:
            print(f"OK: {p}")
    
    # Check .gitkeep files
    data_dirs = ["data/raw", "data/processed", "data/results"]
    for dir_name in data_dirs:
        p = CODE_DIR / dir_name / ".gitkeep"
        if not p.exists():
            print(f"MISSING: {p}")
            all_exist = False
        else:
            print(f"OK: {p}")

    return all_exist

def main():
    """Main entry point."""
    print("--- T001: Initialize Project Directory Structure ---")
    
    # Ensure base code directory exists
    CODE_DIR.mkdir(parents=True, exist_ok=True)
    
    create_directories()
    create_gitkeep()
    
    if verify_structure():
        print("\nVerification PASSED: All directories and .gitkeep files exist.")
        return 0
    else:
        print("\nVerification FAILED: Some directories or files are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())