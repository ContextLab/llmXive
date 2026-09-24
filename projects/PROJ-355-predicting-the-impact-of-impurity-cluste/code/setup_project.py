import os
import sys
from pathlib import Path
from typing import List, Tuple

def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: The path to the directory.
        
    Returns:
        True if the directory exists or was created successfully, False otherwise.
    """
    try:
        path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}")
        return False

def create_gitkeep(path: Path) -> bool:
    """
    Create a .gitkeep file in the specified directory.
    
    Args:
        path: The path to the .gitkeep file.
        
    Returns:
        True if the file was created successfully, False otherwise.
    """
    try:
        # Ensure parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create the file if it doesn't exist
        if not path.exists():
            path.touch()
        
        return True
    except OSError as e:
        print(f"Error creating .gitkeep file {path}: {e}")
        return False

def setup_directories(directories: List[Path]) -> Tuple[bool, List[str]]:
    """
    Setup a list of directories, creating them and their .gitkeep files.
    
    Args:
        directories: A list of directory paths to create.
        
    Returns:
        A tuple of (success: bool, created_paths: List[str])
    """
    created_paths = []
    success = True
    
    for dir_path in directories:
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
    Main entry point for general directory setup.
    
    Returns:
        0 on success, 1 on failure.
    """
    from config import get_project_root
    
    project_root = get_project_root()
    print(f"Using project root: {project_root}")
    
    # Define directories to create (can be extended for other tasks)
    directories = [
        project_root / "code",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
    ]
    
    success, created_paths = setup_directories(directories)
    
    if success:
        print("Successfully created directories:")
        for path in created_paths:
            print(f"  - {path}")
        return 0
    else:
        print("Failed to create one or more directories.")
        return 1

if __name__ == "__main__":
    sys.exit(main())