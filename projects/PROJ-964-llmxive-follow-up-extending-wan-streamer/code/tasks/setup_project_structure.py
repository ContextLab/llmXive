"""
Task T005: Create the project-specific directory structure for PROJ-964.

This script creates the root directory for the specific project 
'PROJ-964-llmxive-follow-up-extending-wan-streamer' and its essential 
subdirectories to organize code, data, tests, and documentation 
specific to this research iteration.

Verification: Run `os.path.exists` on the created paths and assert True.
"""
import os
import sys
from pathlib import Path
from typing import List, Tuple

# Define the project root directory name
PROJECT_ID = "PROJ-964-llmxive-follow-up-extending-wan-streamer"

# Define the relative path from the repository root (where this script is run)
# The project structure is typically at the root of the repo for this specific task
# based on the task description: "Create `projects/PROJ-...` directory structure"
PROJECT_ROOT_DIR = Path("projects") / PROJECT_ID

# Subdirectories to create within the project root
# These organize the specific outputs for this follow-up study
SUBDIRS = [
    "src",           # Source code specific to this project iteration
    "tests",         # Tests specific to this project iteration
    "data",          # Data artifacts specific to this project
    "data/raw",      # Raw data fetched or extracted
    "data/processed",# Processed data for modeling
    "data/models",   # Model checkpoints
    "data/metrics",  # Evaluation metrics
    "docs",          # Project documentation
    "state",         # State tracking for this project
    "contracts",     # Schema contracts
]

def create_directory_structure(base_path: Path, dirs: List[str]) -> List[Tuple[str, bool]]:
    """
    Creates a list of directories relative to base_path.
    
    Args:
        base_path: The root directory to start creating from.
        dirs: List of relative directory paths to create.
        
    Returns:
        A list of tuples (path_str, success_bool).
    """
    results = []
    for d in dirs:
        full_path = base_path / d
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            results.append((str(full_path), True))
            print(f"Created directory: {full_path}")
        except OSError as e:
            results.append((str(full_path), False))
            print(f"Failed to create directory {full_path}: {e}", file=sys.stderr)
    return results

def verify_directories(paths: List[Tuple[str, bool]]) -> bool:
    """
    Verifies that all created directories exist using os.path.exists.
    
    Args:
        paths: List of (path_str, success_bool) from creation.
        
    Returns:
        True if all exist, False otherwise.
    """
    all_exist = True
    for path_str, created in paths:
        exists = os.path.exists(path_str)
        is_dir = os.path.isdir(path_str)
        status = "OK" if (exists and is_dir) else "MISSING"
        print(f"Verification [{status}]: {path_str}")
        if not (exists and is_dir):
            all_exist = False
    return all_exist

def main():
    """
    Main entry point for T005.
    Creates the project structure and verifies existence.
    """
    print(f"Starting T005: Creating project structure for {PROJECT_ID}...")
    print(f"Target root: {PROJECT_ROOT_DIR}")
    
    # Ensure the parent 'projects' directory exists
    PROJECT_ROOT_DIR.parent.mkdir(parents=True, exist_ok=True)
    
    # Create the project root itself
    PROJECT_ROOT_DIR.mkdir(parents=True, exist_ok=True)
    print(f"Created project root: {PROJECT_ROOT_DIR}")
    
    # Create subdirectories
    creation_results = create_directory_structure(PROJECT_ROOT_DIR, SUBDIRS)
    
    # Verify
    success = verify_directories(creation_results)
    
    if success:
        print("\n✅ T005 Verification PASSED: All directories exist.")
        return 0
    else:
        print("\n❌ T005 Verification FAILED: Some directories missing.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
