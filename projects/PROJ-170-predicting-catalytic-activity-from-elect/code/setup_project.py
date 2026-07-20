import os
import sys
from pathlib import Path
from config import get_project_root

def create_directories():
    """
    Creates the required project directory structure as defined in T001a.
    
    Directories created:
    - data/raw/
    - data/processed/
    - code/
    - outputs/
    - tests/
    - state/projects/
    - code/models/
    
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    root = get_project_root()
    if root is None:
        raise RuntimeError("Project root could not be determined. Ensure CONFIG_PATH is set.")
    
    root_path = Path(root)
    
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "outputs",
        "tests",
        "state/projects",
        "code/models"
    ]
    
    created_count = 0
    for dir_name in required_dirs:
        dir_path = root_path / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Directory created/verified: {dir_path}")
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
            return False
    
    print(f"Successfully created/verified {created_count} directories.")
    return True

def main():
    """Entry point for the setup script."""
    success = create_directories()
    if not success:
        sys.exit(1)
    sys.exit(0)

if __name__ == "__main__":
    main()
