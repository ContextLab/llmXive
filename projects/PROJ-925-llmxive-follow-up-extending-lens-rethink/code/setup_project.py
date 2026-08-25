import os
import sys
from pathlib import Path

def create_structure(project_root: Path) -> None:
    """
    Creates the required directory structure for the project.
    
    Creates:
    - data/raw
    - data/processed
    - code (already exists as parent)
    - code/tests
    - code/utils
    - code/models
    - docs
    
    Note: data/ and code/ are sibling directories at the project root.
    """
    directories = [
        "data/raw",
        "data/processed",
        "code/tests",
        "code/utils",
        "code/models",
        "docs",
    ]
    
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def main() -> None:
    """Main entry point for structure creation."""
    # Determine project root (parent of code/ directory)
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent
    
    print(f"Project root: {project_root}")
    create_structure(project_root)
    print("Directory structure creation complete.")

if __name__ == "__main__":
    main()