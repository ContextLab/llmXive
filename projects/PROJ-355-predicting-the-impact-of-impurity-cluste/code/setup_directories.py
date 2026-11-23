import os
import sys
from pathlib import Path
from typing import List, Tuple
from setup_project import ensure_directory, create_gitkeep, setup_directories, main

def setup_data_and_results_directories(project_root: Path) -> List[Tuple[str, bool]]:
    """
    Setup specific data and results directories required by T008.
    Creates data/raw, data/processed, and results with .gitkeep files.
    
    Args:
        project_root: The root path of the project.
        
    Returns:
        A list of tuples (path, created) indicating status.
    """
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
    ]
    
    results = []
    for dir_path in directories:
        created = ensure_directory(dir_path)
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            created = True
        results.append((str(dir_path.relative_to(project_root)), created))
        
    return results

def main():
    """Main entry point for T008 directory setup."""
    from setup_project import get_project_root
    
    project_root = get_project_root()
    print(f"Setting up data and results directories in {project_root}")
    
    results = setup_data_and_results_directories(project_root)
    
    for path_str, created in results:
        status = "created" if created else "exists"
        print(f"  {path_str}: {status}")
        
    print("T008 directory setup complete.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
