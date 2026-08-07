"""
Project Directory Initialization Script.

Creates the full project directory tree for PROJ-191 in a single atomic operation.
This script is idempotent and safe to run multiple times.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the required directory structure for the project."""
    # Define the project root relative to the script location or current working directory
    # The task specifies the root as: projects/PROJ-191-investigating-the-validity-of-the-invers/
    # We assume this script runs from the repository root or the project root context.
    # To be safe and relative to the standard project layout described:
    
    # Base path assumption: The script is in code/, so we go up to root, then into projects/
    # However, the task says "at the repository root: projects/PROJ-191..."
    # Let's assume the script is run from the repository root.
    # If the script is executed as `python code/setup_dirs.py`, CWD is usually the repo root.
    
    repo_root = Path.cwd()
    project_root = repo_root / "projects" / "PROJ-191-investigating-the-validity-of-the-invers"
    
    directories = [
        # Top level
        "code",
        "tests",
        "data",
        "docs",
        
        # Code subdirectories
        "code/data",
        "code/models",
        "code/inference",
        "code/robustness",
        "code/utils",
        
        # Data subdirectories
        "data/raw",
        "data/processed",
        "data/results",
        
        # Test subdirectories
        "tests/unit",
        "tests/contract",
        "tests/integration",
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Initializing project structure at: {project_root}")
    
    for dir_name in directories:
        full_path = project_root / dir_name
        
        # Create parents if they don't exist (atomic mkdir -p behavior)
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            if full_path.exists() and full_path.is_dir():
                created_count += 1
                print(f"  Created: {full_path}")
            else:
                print(f"  Warning: Could not create {full_path}")
        except OSError as e:
            print(f"  Error creating {full_path}: {e}")
            sys.exit(1)
    
    # Verify the structure
    print(f"\nSuccessfully created {created_count} directories.")
    
    # List the structure for verification
    print("\nDirectory structure created:")
    for dir_name in sorted(directories):
        print(f"  {project_root / dir_name}/")
        
    return 0

if __name__ == "__main__":
    sys.exit(main())
