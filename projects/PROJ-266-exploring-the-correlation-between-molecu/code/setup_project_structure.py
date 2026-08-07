import os
import sys
from pathlib import Path
from typing import List

def get_project_root() -> Path:
    """
    Returns the root directory of the project.
    Assumes this script is run from the project root or a subdirectory within it.
    """
    return Path(__file__).resolve().parent.parent

def create_directory_structure(project_root: Path) -> List[Path]:
    """
    Creates the standard project directory structure:
    - code/
    - tests/
    - data/raw/
    - data/processed/
    - data/figures/
    - specs/001-molecular-flexibility-permeability/

    Returns a list of created directory paths.
    """
    directories = [
        project_root / "code",
        project_root / "tests",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "figures",
        project_root / "specs" / "001-molecular-flexibility-permeability",
    ]

    created_dirs = []
    for dir_path in directories:
        if not dir_path.exists():
            os.makedirs(dir_path, exist_ok=True)
            created_dirs.append(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

    return created_dirs

def main():
    """
    Main entry point for creating the project structure.
    """
    project_root = get_project_root()
    print(f"Project root: {project_root}")
    created_dirs = create_directory_structure(project_root)
    
    if created_dirs:
        print(f"\nSuccessfully created {len(created_dirs)} directories.")
    else:
        print("\nAll directories already existed.")
    
    # Verification
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/figures",
        "specs/001-molecular-flexibility-permeability"
    ]
    
    all_exist = True
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.is_dir():
            print(f"ERROR: Missing required directory: {dir_path}")
            all_exist = False
    
    if all_exist:
        print("\nVerification passed: All required directories exist.")
    else:
        print("\nVerification failed: Some required directories are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()
