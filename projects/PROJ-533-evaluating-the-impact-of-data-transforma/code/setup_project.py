"""
Master setup script to initialize the project directory structure.
This script orchestrates the creation of all required top-level directories.
"""
import os
import sys
from pathlib import Path

def main():
    """Create all required project directories."""
    project_root = Path(__file__).resolve().parent.parent
    print(f"Project root: {project_root}")
    
    # Define directories to create
    directories = [
        "code",
        "data",
        "results",
        "tests"
    ]
    
    created = []
    skipped = []
    
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_path)
            print(f"Created: {dir_path}")
        else:
            skipped.append(dir_path)
            print(f"Exists: {dir_path}")
    
    print(f"\nSummary: {len(created)} directories created, {len(skipped)} already existed.")
    
    # Create __init__.py files to make them packages
    for dir_name in directories:
        dir_path = project_root / dir_name
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created: {init_file}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())