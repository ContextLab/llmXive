"""
Setup script for the Memory Load-Adaptive Text Presentation project.

Creates the required directory structure as defined in the implementation plan:
- data/raw: For raw downloaded datasets
- data/derived: For processed and derived data artifacts
- code: For Python modules and scripts
- tests: For unit and integration tests
- results: For analysis outputs and reports
- data/metadata: For dataset metadata and configuration
- figures: For generated plots and visualizations
- specs: For specification documents
- docs: For project documentation
"""

import os
import sys
from pathlib import Path

def create_directory_structure(root_path: Path) -> None:
    """
    Create the project directory structure.
    
    Args:
        root_path: The root directory where the structure will be created.
    """
    directories = [
        "data/raw",
        "data/derived",
        "code",
        "tests/unit",
        "tests/integration",
        "results",
        "data/metadata",
        "figures",
        "specs",
        "docs",
        "code/utils",
        "code/report_assets",
    ]
    
    created = []
    for dir_path in directories:
        full_path = root_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created.append(dir_path)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
    
    if not created:
        print("All directories already exist.")
    else:
        print(f"\nSuccessfully created {len(created)} directories.")

def create_gitkeep_files(root_path: Path) -> None:
    """
    Create .gitkeep files in all directories to ensure they are tracked by git.
    
    Args:
        root_path: The root directory of the project.
    """
    directories = [
        "data/raw",
        "data/derived",
        "code",
        "tests/unit",
        "tests/integration",
        "results",
        "data/metadata",
        "figures",
        "specs",
        "docs",
        "code/utils",
        "code/report_assets",
    ]
    
    for dir_path in directories:
        full_path = root_path / dir_path
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {dir_path}")

def main():
    """Main entry point for the setup script."""
    # Determine the root path (project root where this script is located)
    script_dir = Path(__file__).parent
    root_path = script_dir.parent  # Go up one level from code/
    
    print(f"Setting up project structure in: {root_path}")
    print("-" * 50)
    
    create_directory_structure(root_path)
    create_gitkeep_files(root_path)
    
    print("-" * 50)
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
