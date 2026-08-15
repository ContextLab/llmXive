import os
import sys
from pathlib import Path

def create_directory(path: str) -> bool:
    """
    Creates a directory at the specified path if it does not already exist.
    
    Args:
        path: The absolute or relative path to the directory to create.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    dir_path = Path(path)
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except OSError as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main function to create all required project directories.
    """
    base_dir = Path(__file__).parent.parent
    
    directories = [
        base_dir / "scripts",
        base_dir / "data" / "raw",
        base_dir / "data" / "processed",
        base_dir / "data" / "splits",
        base_dir / "models",
        base_dir / "tests"
    ]
    
    all_success = True
    for dir_path in directories:
        success = create_directory(str(dir_path))
        status = "Created" if success else "Failed"
        print(f"{status}: {dir_path}")
        if not success:
            all_success = False
    
    if not all_success:
        sys.exit(1)

if __name__ == "__main__":
    main()
