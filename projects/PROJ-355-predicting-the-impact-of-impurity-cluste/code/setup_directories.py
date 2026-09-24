import os
import sys
from pathlib import Path
from typing import List, Tuple
from setup_project import ensure_directory, create_gitkeep, setup_directories, main

def setup_data_and_results_directories(project_root: Path) -> Tuple[bool, List[str]]:
    """
    Setup the specific data and results directory structure required for T008.
    
    Creates:
    - data/raw/
    - data/processed/
    - results/
    
    Each directory will contain a .gitkeep file to ensure they are tracked by git.
    
    Args:
        project_root: The root path of the project.
        
    Returns:
        A tuple of (success: bool, created_paths: List[str])
    """
    directories_to_create = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
    ]
    
    created_paths = []
    success = True
    
    for dir_path in directories_to_create:
        if ensure_directory(dir_path):
            gitkeep_path = dir_path / ".gitkeep"
            if create_gitkeep(gitkeep_path):
                created_paths.append(str(dir_path))
            else:
                success = False
                print(f"Failed to create .gitkeep in {dir_path}")
        else:
            success = False
            print(f"Failed to create directory {dir_path}")
    
    return success, created_paths

def main() -> int:
    """
    Main entry point for T008 execution.
    
    Returns:
        0 on success, 1 on failure.
    """
    from config import get_project_root
    
    project_root = get_project_root()
    print(f"Setting up data and results directories in: {project_root}")
    
    success, created_paths = setup_data_and_results_directories(project_root)
    
    if success:
        print("Successfully created directories:")
        for path in created_paths:
            print(f"  - {path}")
        print("All directories contain .gitkeep files.")
        return 0
    else:
        print("Failed to create one or more directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
