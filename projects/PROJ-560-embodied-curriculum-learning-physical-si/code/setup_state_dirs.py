import os
import sys
from pathlib import Path

def create_directory(path: str) -> bool:
    """
    Create a directory at the specified path if it does not already exist.

    Args:
        path: The absolute or relative path to the directory to create.

    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    dir_path = Path(path)
    try:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")
        return True
    except OSError as e:
        print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point for creating state directories for the project.
    Creates the specific state directory for PROJ-560.
    """
    # Define the project root relative to the script location or CWD
    # Assuming the script is run from the project root or code/ directory
    project_root = Path.cwd()
    
    # Define the specific state directory path as per task T001c
    state_dir = project_root / "state" / "projects" / "PROJ-560-embodied-curriculum-learning-physical-si"
    
    print(f"Ensuring state directory exists: {state_dir}")
    success = create_directory(str(state_dir))
    
    if not success:
        sys.exit(1)
    
    # Verify creation
    if state_dir.exists() and state_dir.is_dir():
        print(f"Successfully verified state directory: {state_dir}")
        sys.exit(0)
    else:
        print(f"Failed to verify state directory creation: {state_dir}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()