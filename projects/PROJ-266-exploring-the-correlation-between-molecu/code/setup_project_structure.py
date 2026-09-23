"""
T002: Create project structure per implementation plan.

Requirement: Execute os.makedirs('code/', exist_ok=True),
os.makedirs('tests/', exist_ok=True), os.makedirs('data/', exist_ok=True).
"""
import os
import sys
from pathlib import Path


def create_directories():
    """Create the core project directories: code/, tests/, data/."""
    # Get the project root (parent of the code/ directory)
    # We assume this script is run from the project root or code/
    project_root = Path.cwd()
    
    directories = [
        project_root / "code",
        project_root / "tests",
        project_root / "data",
    ]
    
    created = []
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        created.append(str(dir_path))
        print(f"Created directory: {dir_path}")
    
    # Verify creation (explicit requirement)
    for dir_path in directories:
        assert dir_path.is_dir(), f"Failed to create directory: {dir_path}"
    
    return created


def main():
    """Entry point for the script."""
    print("T002: Creating project structure...")
    try:
        created_dirs = create_directories()
        print(f"Success. Created directories: {created_dirs}")
        return 0
    except Exception as e:
        print(f"Error creating directories: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
