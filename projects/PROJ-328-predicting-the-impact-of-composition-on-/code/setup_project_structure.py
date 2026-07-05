"""
Script to create the project directory structure for PROJ-328.
This implements Task T001: Create project directory structure per implementation plan.

Creates the following directories relative to the project root:
- projects/PROJ-328-predicting-the-impact-of-composition-on-/data/
- projects/PROJ-328-predicting-the-impact-of-composition-on-/code/
- projects/PROJ-328-predicting-the-impact-of-composition-on-/tests/
- projects/PROJ-328-predicting-the-impact-of-composition-on-/models/
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to the current working directory
    # We assume this script is run from the repository root
    project_root = Path.cwd()
    
    # Define the specific project directory name as per tasks.md
    project_name = "PROJ-328-predicting-the-impact-of-composition-on-"
    project_path = project_root / "projects" / project_name
    
    # Define the subdirectories required by T001
    subdirectories = [
        "data",
        "code",
        "tests",
        "models"
    ]
    
    created_paths = []
    
    print(f"Creating project structure at: {project_path}")
    
    # Create the main project directory
    project_path.mkdir(parents=True, exist_ok=True)
    created_paths.append(project_path)
    
    # Create subdirectories
    for subdir in subdirectories:
        dir_path = project_path / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        created_paths.append(dir_path)
        print(f"  Created: {dir_path}")
    
    # Create __init__.py files in Python packages to make them importable
    # This is good practice even if not strictly required by the task description
    for subdir in ["code", "tests", "models"]:
        init_file = project_path / subdir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            created_paths.append(init_file)
            print(f"  Created: {init_file}")
    
    # Create .gitkeep files in data directory to ensure it's tracked by git
    # even if it's empty
    data_dir = project_path / "data"
    gitkeep_file = data_dir / ".gitkeep"
    if not gitkeep_file.exists():
        gitkeep_file.touch()
        created_paths.append(gitkeep_file)
        print(f"  Created: {gitkeep_file}")
    
    print(f"\nSuccessfully created {len(created_paths)} directories/files.")
    print(f"Project structure is ready for PROJ-328.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
