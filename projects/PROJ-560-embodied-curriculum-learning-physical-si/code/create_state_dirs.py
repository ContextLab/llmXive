import os
import sys
from pathlib import Path

def create_directory(path: str) -> bool:
    """
    Create a directory if it does not exist.
    
    Args:
        path: The path to the directory to create.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    try:
        dir_path = Path(path)
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Directory created/exists: {dir_path.resolve()}")
        return True
    except Exception as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main function to create state directories for the project.
    """
    project_root = Path(__file__).resolve().parent.parent
    state_base = project_root / "state"
    project_state = state_base / "projects" / "PROJ-560-embodied-curriculum-learning-physical-si"
    
    print(f"Creating state directories under: {project_state}")
    
    if create_directory(str(project_state)):
        # Create standard subdirectories for state management
        subdirs = [
            "runs",
            "checkpoints",
            "logs",
            "artifacts"
        ]
        
        for subdir in subdirs:
            subdir_path = project_state / subdir
            if not create_directory(str(subdir_path)):
                print(f"Warning: Failed to create subdirectory {subdir_path}", file=sys.stderr)
        
        print("State directory structure initialization complete.")
        return 0
    else:
        print("Failed to create state directory structure.", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())