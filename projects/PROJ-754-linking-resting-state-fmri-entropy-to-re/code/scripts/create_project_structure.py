import os
import sys
from pathlib import Path
from typing import Optional

def get_project_root() -> Path:
    """
    Determine the project root directory.
    
    Looks for the project root by checking for a .git directory,
    or defaults to the current working directory if not found.
    
    Returns:
        Path: The project root directory path.
    """
    current = Path.cwd()
    
    # Walk up the directory tree looking for .git
    for parent in [current, *current.parents]:
        if (parent / ".git").exists():
            return parent
        
        # Also check for common project markers
        if (parent / "requirements.txt").exists():
            return parent
    
    # Fallback to current directory
    return current

def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: The directory path to ensure exists.
        
    Returns:
        bool: True if the directory exists after the call (created or pre-existing).
    """
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            return True
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main function to create the project directory structure.
    
    Creates the following directories relative to the project root:
    - src/data, src/analysis, src/stats, src/config, src/utils, src/entities
    - tests/unit, tests/integration
    """
    project_root = get_project_root()
    print(f"Project root: {project_root}")
    
    # Define the directories to create for T002
    directories = [
        # Source subdirectories
        project_root / "src" / "data",
        project_root / "src" / "analysis",
        project_root / "src" / "stats",
        project_root / "src" / "config",
        project_root / "src" / "utils",
        project_root / "src" / "entities",
        
        # Test subdirectories
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
    ]
    
    success = True
    for dir_path in directories:
        if ensure_directory(dir_path):
            print(f"Created/Verified: {dir_path.relative_to(project_root)}")
        else:
            print(f"Failed to create: {dir_path.relative_to(project_root)}", file=sys.stderr)
            success = False
    
    if success:
        print("Directory structure creation completed successfully.")
        sys.exit(0)
    else:
        print("Directory structure creation had errors.", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()