"""
Setup script to create the required project directory structure.
This script creates code/src/, code/tests/, data directories, and state directories.
"""
import os
import sys
from pathlib import Path

def create_directory(path: Path, description: str = "") -> bool:
    """
    Create a directory if it does not exist.
    
    Args:
        path: The Path object representing the directory to create.
        description: Optional description for logging.
        
    Returns:
        True if directory was created or already exists, False on error.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        if description:
            print(f"Created directory: {path} ({description})")
        else:
            print(f"Created directory: {path}")
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main function to create the project directory structure.
    """
    # Define the project root (assuming script is run from project root or code/)
    # We will use the current working directory as the base
    base_dir = Path.cwd()
    
    # If running from code/, adjust base_dir to parent
    if base_dir.name == "code":
        base_dir = base_dir.parent
    
    print(f"Base directory: {base_dir}")
    
    # Phase 1: Setup - Code Directories (T001a)
    code_dirs = [
        (base_dir / "code" / "src", "Source code directory"),
        (base_dir / "code" / "tests", "Test directory"),
    ]
    
    # Phase 1: Setup - Data Directories (T001b)
    data_dirs = [
        (base_dir / "data" / "raw", "Raw input data"),
        (base_dir / "data" / "processed", "Processed data"),
        (base_dir / "data" / "synthetic", "Synthetic generated data"),
        (base_dir / "data" / "derivation_logs", "Logs for data derivation/skipping"),
    ]
    
    # Phase 1: Setup - State Directories (T001c)
    project_id = "PROJ-560-embodied-curriculum-learning-physical-si"
    state_dirs = [
        (base_dir / "state" / "projects" / project_id, "Project state directory"),
    ]
    
    all_dirs = code_dirs + data_dirs + state_dirs
    
    success = True
    for path, desc in all_dirs:
        if not create_directory(path, desc):
            success = False
    
    if success:
        print("\nAll directories created successfully.")
        print("Directory structure:")
        print(f"  code/")
        print(f"    src/")
        print(f"    tests/")
        print(f"  data/")
        print(f"    raw/")
        print(f"    processed/")
        print(f"    synthetic/")
        print(f"    derivation_logs/")
        print(f"  state/")
        print(f"    projects/")
        print(f"      {project_id}/")
        sys.exit(0)
    else:
        print("\nFailed to create some directories.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()