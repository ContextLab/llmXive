"""
Script to initialize the project directory structure as defined in plan.md.

This script creates the necessary folders for code organization, data storage,
testing, and contracts. It is idempotent and safe to run multiple times.

Target Structure:
- code/
- data/raw/
- data/processed/
- data/results/
- tests/
- contracts/
"""
import os
import sys
from pathlib import Path

# Define the relative paths to create based on plan.md specifications
DIRECTORIES = [
    "code",
    "data/raw",
    "data/processed",
    "data/results",
    "tests",
    "contracts",
    # Subdirectories for better organization
    "tests/unit",
    "tests/integration",
    "tests/contract",
    "specs",
    "scripts",
    "figures",
]

def create_directory_structure(base_path: Path) -> list:
    """
    Creates the directory structure relative to the base_path.
    
    Args:
        base_path: The root directory where structures should be created.
        
    Returns:
        A list of created directory paths as strings.
    """
    created_dirs = []
    for dir_name in DIRECTORIES:
        full_path = base_path / dir_name
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(full_path))
                print(f"Created directory: {full_path}")
            else:
                print(f"Directory already exists: {full_path}")
        except PermissionError:
            print(f"Error: Permission denied creating {full_path}", file=sys.stderr)
            return []
        except OSError as e:
            print(f"Error: Could not create {full_path}: {e}", file=sys.stderr)
            return []
    
    return created_dirs

def main():
    """Main entry point for the script."""
    # Determine the project root (parent of the scripts directory)
    # Assuming this script is located at scripts/init_repo.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    print(f"Initializing project structure at: {project_root}")
    
    created = create_directory_structure(project_root)
    
    if created:
        print(f"\nSuccessfully created {len(created)} directories.")
    else:
        print("\nNo new directories created (may have failed).")
        sys.exit(1)

if __name__ == "__main__":
    main()