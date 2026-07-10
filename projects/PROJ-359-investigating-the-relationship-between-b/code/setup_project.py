import os
import sys
from pathlib import Path

def create_project_structure():
    """
    Create the required project directory structure for PROJ-359.
    Paths are relative to the project root where this script is executed.
    """
    # Define the base project directory as per task description
    # The task asks for: projects/PROJ-359-investigating-the-relationship-between-b/code/
    # However, the existing API surface shows files in 'code/' at the root.
    # To align with the "Existing project API surface" provided (which assumes 'code/' exists),
    # and the task requirement to create structure "per implementation plan",
    # we will ensure the 'code/' directory and its subdirectories exist.
    # The task description mentions a nested path, but the provided file list implies
    # the project root is where 'code/' resides. We will create the structure relative to 'code/'.
    
    base_dir = Path("code")
    
    # Define subdirectories as requested in T001
    subdirs = [
        "src",
        "tests",
        "data/raw",
        "data/preprocessed",
        "data/results",
        "data/logs",
        "data/motion"
    ]
    
    created_dirs = []
    for subdir in subdirs:
        dir_path = base_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(dir_path))
        print(f"Created directory: {dir_path}")
    
    # Create __init__.py files to make directories proper Python packages
    # for src and tests
    (base_dir / "src" / "__init__.py").touch(exist_ok=True)
    (base_dir / "tests" / "__init__.py").touch(exist_ok=True)
    
    # Create a placeholder .gitkeep in data directories to ensure they are tracked
    # even if empty (though they will be filled by later tasks)
    data_dirs = ["raw", "preprocessed", "results", "logs", "motion"]
    for d in data_dirs:
        (base_dir / "data" / d / ".gitkeep").touch(exist_ok=True)
        
    return created_dirs

def main():
    """Entry point for the project setup script."""
    print("Initializing project structure for PROJ-359...")
    created = create_project_structure()
    print(f"Project structure initialized. Created {len(created)} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
