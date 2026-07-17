import os
import sys
from pathlib import Path

def main():
    """
    Creates the project directory structure for PROJ-258.
    
    Directories created:
    - code/
    - data/raw/
    - data/interim/
    - data/processed/
    - tests/
    - reports/
    - docs/
    - .github/workflows/
    """
    # Define the project root (parent of this script's location or current dir)
    # We assume this script is run from the project root or code/
    project_root = Path.cwd()
    
    # Define required directories relative to project root
    directories = [
        "code",
        "data/raw",
        "data/interim",
        "data/processed",
        "tests",
        "reports",
        "docs",
        ".github/workflows",
        "specs"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Create .gitkeep files in data directories to ensure they are tracked
    data_dirs = ["data/raw", "data/interim", "data/processed"]
    for dir_name in data_dirs:
        dir_path = project_root / dir_name
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {dir_path}")
    
    print(f"\nProject structure initialization complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
