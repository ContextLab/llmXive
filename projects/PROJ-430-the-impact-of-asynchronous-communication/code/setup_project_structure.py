"""
Setup Project Structure for PROJ-430-the-impact-of-asynchronous-communication.

This module initializes the root project directory and creates the necessary
subdirectories (code/, data/, tests/, docs/) as required by T001a and T001b.
It also ensures the data subdirectories (raw/, derived/, validation/, logs/)
are created for T006.
"""
import os
import sys
from pathlib import Path

# Import config to get project root path logic if needed, 
# though for T001a we define the root explicitly based on task description.
# The task specifies: projects/PROJ-430-the-impact-of-asynchronous-communication/

def ensure_directory_exists(dir_path: Path) -> None:
    """Create a directory if it does not exist."""
    if not dir_path.exists():
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    else:
        print(f"Directory already exists: {dir_path}")

def main() -> int:
    """
    Main entry point to create the project structure.
    
    Creates:
    - projects/PROJ-430-the-impact-of-asynchronous-communication/
    - code/, data/, tests/, docs/ inside the project root
    - data/raw/, data/derived/, data/validation/, data/logs/
    - .gitkeep in data/validation/
    - .gitignore in data/ to exclude *.csv, *.json in raw
    """
    # Define the project root as specified in T001a
    # Assuming this script runs from the repository root
    repo_root = Path.cwd()
    project_root = repo_root / "projects" / "PROJ-430-the-impact-of-asynchronous-communication"
    
    print(f"Initializing project at: {project_root}")
    
    # T001a: Create project root directory
    ensure_directory_exists(project_root)
    
    # T001b: Create main subdirectories
    subdirs = ["code", "data", "tests", "docs"]
    for subdir in subdirs:
        ensure_directory_exists(project_root / subdir)
    
    # T006: Create data subdirectories
    data_root = project_root / "data"
    data_subdirs = ["raw", "derived", "validation", "logs"]
    for subdir in data_subdirs:
        ensure_directory_exists(data_root / subdir)
    
    # T006: Create .gitkeep in data/validation/
    validation_dir = data_root / "validation"
    gitkeep_file = validation_dir / ".gitkeep"
    if not gitkeep_file.exists():
        gitkeep_file.touch()
        print(f"Created .gitkeep in {validation_dir}")
    
    # T006: Create .gitignore in data/ to exclude raw CSV/JSON
    gitignore_file = data_root / ".gitignore"
    gitignore_content = """# Exclude raw data files from version control
*.csv
*.json
*.parquet
*.log

# Keep validation directory structure
!validation/.gitkeep
"""
    if not gitignore_file.exists():
        gitignore_file.write_text(gitignore_content)
        print(f"Created .gitignore in {data_root}")
    
    print("Project structure initialization complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())