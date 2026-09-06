"""
Script to initialize the project directory structure for PROJ-397.
Creates required directories and .gitkeep files as per T001.
"""
import os
import sys
from pathlib import Path

def main():
    """Create the project directory structure and .gitkeep files."""
    # Define the project root relative to the code directory
    # The task specifies: projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/...
    # Since this script is in code/, we assume the project root is one level up or
    # we are operating within the code/ directory structure defined in tasks.md.
    # tasks.md says: "Create directories `projects/PROJ-397.../code/data/`..."
    # Assuming the current working directory is the project root or we construct the path.
    # To be safe and portable, we construct the path relative to this script's location
    # if it's inside the code folder, or assume the project root is the parent of 'code'.
    
    script_path = Path(__file__).resolve()
    # If this file is at code/setup_directories.py, the project root is script_path.parent.parent
    # However, tasks.md implies the project root is `projects/PROJ-397...`
    # Let's assume the script is run from the project root or we define the root explicitly.
    # Based on the path conventions in tasks.md: "Single project: `src/`, `tests/` at repository root"
    # But the specific task T001 path is `projects/PROJ-397.../code/...`
    # Let's assume the project root is `projects/PROJ-397-predicting-avian-foraging-behavior-from-`
    # and we are running this from inside `code/` or the script handles the path.
    
    # We will define the base path as the directory containing 'code' if we are inside 'code',
    # or assume the current working directory is the project root.
    # To ensure robustness, we check if we are in 'code' and go up one level.
    if script_path.name == 'code':
        project_root = script_path.parent
    else:
        # If the script is directly in code/, parent is code, parent.parent is project root
        # But the path in tasks.md is `projects/.../code/`.
        # Let's assume the script is run from the project root.
        project_root = Path.cwd()
    
    # If the project root doesn't look like the expected project, we might need to adjust.
    # However, the task explicitly lists the path: `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/...`
    # Let's assume the script is run from the project root `projects/PROJ-397...`
    
    # Define the directories to create relative to the `code` directory
    # The task says: `projects/PROJ-397.../code/data/`, `models/`, `viz/`, etc.
    # This implies these are subdirectories of `code/`.
    
    code_dir = project_root / "code"
    
    # If the script is run from the project root, code_dir exists.
    # If the script is in code/, we might need to adjust.
    # Let's assume the standard execution: run from project root.
    
    directories = [
        "data",
        "models",
        "viz",
        "notebooks",
        "utils",
        "tests"
    ]
    
    created_dirs = []
    
    for dir_name in directories:
        dir_path = code_dir / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
            
            # Create .gitkeep file
            gitkeep_path = dir_path / ".gitkeep"
            gitkeep_path.touch()
            print(f"Created directory: {dir_path}")
            print(f"Created .gitkeep: {gitkeep_path}")
        except PermissionError:
            print(f"Error: Permission denied creating {dir_path}")
            return 1
        except Exception as e:
            print(f"Error creating {dir_path}: {e}")
            return 1
    
    print(f"Successfully created {len(created_dirs)} directories with .gitkeep files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())