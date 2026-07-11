"""
Script to initialize the project directory structure for PROJ-811.
Creates the necessary folders for code, data, tests, specs, and artifacts.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to where this script runs
    # Assuming this script is at code/scripts/setup_project_structure.py
    # The project root is two levels up: code/scripts -> code -> root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent
    
    # Define the directory structure to create
    # Based on standard Python project layout and task requirements
    directories = [
        # Source Code
        "code/src",
        "code/scripts",
        
        # Tests
        "code/tests",
        
        # Data Storage
        "data/raw",
        "data/processed",
        "data/results",
        
        # Artifacts & Checksums
        "artifacts",
        
        # Specifications & Docs
        "specs",
        "docs",
        
        # Configuration
        "config",
        
        # Figures/Outputs
        "figures",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path.relative_to(project_root)}")
            created_count += 1
        else:
            # Ensure it's a directory, not a file
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    # Create placeholder .gitkeep files to ensure directories are tracked by git
    # and to satisfy the "real files" requirement for the structure
    gitkeep_content = "# Keep this directory in version control\n"
    for dir_path in directories:
        full_path = project_root / dir_path
        gitkeep_file = full_path / ".gitkeep"
        if not gitkeep_file.exists():
            gitkeep_file.write_text(gitkeep_content)
            created_count += 1

    print(f"\nProject structure initialized. Created/Verified {created_count} paths.")
    print(f"Project Root: {project_root}")

if __name__ == "__main__":
    main()
