#!/usr/bin/env python3
"""
Repository skeleton setup script for PROJ-492.

Creates the required directory structure:
- src/
- tests/
- data/
- output/
- contracts/
- notebooks/
- .github/
- docs/

Usage: python code/setup_project_structure.py
"""
import os
import sys
from pathlib import Path


REQUIRED_DIRECTORIES = [
    "src",
    "tests",
    "data",
    "output",
    "contracts",
    "notebooks",
    ".github",
    "docs",
]

def create_directory_structure(base_path: Path) -> None:
    """Create all required directories under the base path."""
    created = []
    for dir_name in REQUIRED_DIRECTORIES:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_name)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    if created:
        print(f"\nSuccessfully created {len(created)} new directories.")
    else:
        print("\nAll required directories already exist.")


def create_init_files(base_path: Path) -> None:
    """Create __init__.py files for Python package directories."""
    package_dirs = ["src", "tests"]
    for dir_name in package_dirs:
        dir_path = base_path / dir_name
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.write_text("# Package initialization\n")
            print(f"Created {init_file}")


def main() -> int:
    """Main entry point."""
    # Determine base path (project root)
    # Assume script is at code/setup_project_structure.py, so base is parent's parent
    script_path = Path(__file__).resolve()
    base_path = script_path.parent.parent
    
    print(f"Project root: {base_path}")
    print("-" * 50)
    
    create_directory_structure(base_path)
    create_init_files(base_path)
    
    print("-" * 50)
    print("Repository skeleton setup complete.")
    
    # Verify all directories exist
    all_exist = all((base_path / d).exists() for d in REQUIRED_DIRECTORIES)
    if all_exist:
        print("Verification: All required directories exist.")
        return 0
    else:
        print("Verification: Some directories are missing!")
        return 1


if __name__ == "__main__":
    sys.exit(main())
