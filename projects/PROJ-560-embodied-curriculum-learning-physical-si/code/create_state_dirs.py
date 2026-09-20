import os
import sys
from pathlib import Path

def create_directory(path: str) -> bool:
    """
    Creates a directory and all its parent directories if they do not exist.
    Returns True if the directory was created or already exists, False otherwise.
    """
    try:
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main function to create the state directories for the project.
    """
    # Define the base state directory path as per the task requirement
    # The task specifies: projects/PROJ-560-embodied-curriculum-learning-physical-si/state/projects/PROJ-560-embodied-curriculum-learning-physical-si/
    # We assume the script is run from the project root or we construct the path relative to a standard root.
    # To ensure robustness, we will create the directory relative to the current working directory 
    # but structured exactly as requested in the task description.
    
    # The task path is absolute relative to the project root structure defined in T001a/T001b context.
    # We will construct the full path string.
    project_root = Path.cwd()
    state_dir_path = project_root / "state" / "projects" / "PROJ-560-embodied-curriculum-learning-physical-si"
    
    print(f"Creating state directory: {state_dir_path}")
    
    if create_directory(str(state_dir_path)):
        print(f"Successfully created or verified existence of: {state_dir_path}")
        # Verify the directory exists and is a directory
        if state_dir_path.is_dir():
            print("Verification: Directory exists and is valid.")
            return 0
        else:
            print("Verification failed: Path exists but is not a directory.", file=sys.stderr)
            return 1
    else:
        print("Failed to create directory.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())