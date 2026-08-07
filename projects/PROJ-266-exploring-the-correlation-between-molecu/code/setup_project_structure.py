"""
T002: Create project structure per implementation plan.

This script creates the required directory structure:
- code/
- tests/
- data/raw/
- data/processed/
- figures/
- specs/001-molecular-flexibility-permeability/

It also creates empty __init__.py files to ensure Python package recognition.
"""
import os
import sys
from pathlib import Path
from typing import List

def get_project_root() -> Path:
    """Return the project root directory (parent of the code/ directory)."""
    # Assuming this script is run from the project root
    return Path.cwd()

def create_directory_structure(project_root: Path) -> List[Path]:
    """
    Create the required project directories.
    
    Args:
        root: The project root directory.
        
    Returns:
        List of created directory paths.
    """
    directories = [
        root / "code",
        root / "code" / "data",
        root / "code" / "utils",
        root / "tests",
        root / "tests" / "contract",
        root / "data",
        root / "data" / "raw",
        root / "data" / "processed",
        root / "figures",
        root / "specs",
        root / "specs" / "001-molecular-flexibility-permeability",
        root / "specs" / "001-molecular-flexibility-permeability" / "contracts",
        root / "state",
        root / "state" / "projects",
    ]
    
    created = []
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
        created.append(dir_path)
        print(f"Created directory: {dir_path}")
    
    # Create __init__.py files for Python packages
    init_files = [
        root / "code" / "__init__.py",
        root / "code" / "data" / "__init__.py",
        root / "code" / "utils" / "__init__.py",
        root / "tests" / "__init__.py",
        root / "tests" / "contract" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created: {init_file}")
    
    return created

def main() -> int:
    """Main entry point for the script."""
    print("Setting up project structure...")
    root = get_project_root()
    print(f"Project root: {root}")
    
    created_dirs = create_directory_structure(root)
    
    print(f"\nSuccessfully created {len(created_dirs)} directories.")
    print("Project structure is ready.")
    
    # Verify the structure
    required_dirs = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "figures",
        "specs/001-molecular-flexibility-permeability",
    ]
    
    all_present = True
    for rel_dir in required_dirs:
        if not (root / rel_dir).is_dir():
            print(f"ERROR: Missing directory: {rel_dir}")
            all_present = False
    
    if all_present:
        print("\nVerification passed: All required directories exist.")
        return 0
    else:
        print("\nVerification failed: Some directories are missing.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
