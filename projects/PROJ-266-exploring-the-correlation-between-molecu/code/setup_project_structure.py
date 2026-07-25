"""
Setup project structure for llmXive automated science pipeline.
Creates the required directory hierarchy: code/, tests/, data/, data/raw/, data/processed/, figures/, state/.
"""
import os
import sys
from pathlib import Path
from typing import List

def get_project_root() -> Path:
    """
    Returns the project root directory (parent of the 'code' directory).
    Assumes this script is located at code/setup_project_structure.py.
    """
    current_file = Path(__file__).resolve()
    # Go up two levels: code/setup_project_structure.py -> code -> root
    return current_file.parent.parent

def create_directory_structure(root: Path) -> List[str]:
    """
    Creates the standard directory structure for the project.
    Returns a list of created directory paths as strings.
    """
    directories = [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "figures",
        "state",
        "state/projects",
        "specs",
        "docs",
    ]

    created = []
    for dir_name in directories:
        dir_path = root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
        elif not dir_path.is_dir():
            raise RuntimeError(f"Path exists but is not a directory: {dir_path}")
    
    return created

def main():
    """
    Main entry point to create the project structure.
    """
    root = get_project_root()
    print(f"Project root identified at: {root}")
    
    try:
        created_dirs = create_directory_structure(root)
        if created_dirs:
            print(f"Successfully created {len(created_dirs)} directories:")
            for d in created_dirs:
                print(f"  - {d}")
        else:
            print("All required directories already exist.")
        
        print("Project structure setup complete.")
        return 0
    except Exception as e:
        print(f"Error setting up project structure: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
