import os
import sys
from pathlib import Path
from typing import List, Tuple

PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent
PROJECT_NAME = "PROJ-964-llmxive-follow-up-extending-wan-streamer"
PROJECT_PATH = PROJECT_ROOT / "projects" / PROJECT_NAME

def create_directory_structure() -> Tuple[bool, List[str]]:
    """
    Creates the full directory structure for the project under projects/PROJ-964-...
    
    Returns:
        Tuple of (success: bool, created_paths: List[str])
    """
    created_paths = []
    success = True

    # Define the subdirectories relative to the project root
    subdirs = [
        "code",
        "code/data",
        "code/models",
        "code/inference",
        "code/evaluation",
        "code/utils",
        "code/tasks",
        "code/tests",
        "data",
        "data/raw",
        "data/processed",
        "data/models",
        "data/metrics",
        "state",
        "docs",
        "specs",
        "contracts",
        "figures"
    ]

    for subdir in subdirs:
        full_path = PROJECT_PATH / subdir
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_paths.append(str(full_path))
        except OSError as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
            success = False

    return success, created_paths

def verify_directories() -> Tuple[bool, List[str]]:
    """
    Verifies that all required directories exist.
    
    Returns:
        Tuple of (all_exist: bool, missing_paths: List[str])
    """
    missing_paths = []
    
    # Re-define the structure to check
    subdirs = [
        "code",
        "code/data",
        "code/models",
        "code/inference",
        "code/evaluation",
        "code/utils",
        "code/tasks",
        "code/tests",
        "data",
        "data/raw",
        "data/processed",
        "data/models",
        "data/metrics",
        "state",
        "docs",
        "specs",
        "contracts",
        "figures"
    ]

    for subdir in subdirs:
        full_path = PROJECT_PATH / subdir
        if not os.path.isdir(full_path):
            missing_paths.append(str(full_path))

    return len(missing_paths) == 0, missing_paths

def main():
    """
    Main entry point to create and verify the project directory structure.
    """
    print(f"Target Project Path: {PROJECT_PATH}")
    
    # Create directories
    print("Creating directory structure...")
    success, created = create_directory_structure()
    
    if not success:
        print("Failed to create some directories.", file=sys.stderr)
        sys.exit(1)
        
    print(f"Created {len(created)} directories.")
    
    # Verify directories
    print("Verifying directory structure...")
    all_exist, missing = verify_directories()
    
    if not all_exist:
        print(f"Verification failed. Missing directories: {missing}", file=sys.stderr)
        sys.exit(1)
        
    print("Verification successful. All directories exist.")
    print(f"Project structure created at: {PROJECT_PATH}")

if __name__ == "__main__":
    main()
