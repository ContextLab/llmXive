import os
import sys
from pathlib import Path

def create_directory_structure(root_path: Path) -> None:
    """
    Creates the required project directory structure for the Memory Load-Adaptive Text Presentation project.
    
    Directories created:
    - data/raw: For raw, unprocessed data downloads (e.g., from OpenNeuro)
    - data/derived: For processed, cleaned, and feature-engineered data
    - code: For all Python source modules
    - tests: For unit and integration tests
    - results: For final analysis outputs, reports, and figures
    """
    directories = [
        root_path / "data" / "raw",
        root_path / "data" / "derived",
        root_path / "code",
        root_path / "tests",
        root_path / "results",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")

def create_gitkeep_files(root_path: Path) -> None:
    """
    Creates .gitkeep files in all data directories to ensure they are tracked by git
    even when empty.
    """
    data_dirs = [
        root_path / "data" / "raw",
        root_path / "data" / "derived",
    ]
    
    for directory in data_dirs:
        gitkeep_path = directory / ".gitkeep"
        gitkeep_path.touch()
        print(f"Created .gitkeep in: {directory}")

def main() -> None:
    """
    Main entry point for project structure setup.
    Creates all required directories and initializes git tracking for data folders.
    """
    # Determine the project root (assumed to be the directory containing this script's parent)
    # or use current working directory if run directly.
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent
    
    print(f"Setting up project structure at: {project_root}")
    
    create_directory_structure(project_root)
    create_gitkeep_files(project_root)
    
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
