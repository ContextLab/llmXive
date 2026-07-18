import os
import sys
from pathlib import Path

def create_directory(path_str: str) -> bool:
    """
    Create a directory at the given path if it does not exist.
    
    Args:
        path_str: The path string to create.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    try:
        path = Path(path_str)
        path.mkdir(parents=True, exist_ok=True)
        # Verify the directory exists and is actually a directory
        if path.is_dir():
            return True
        else:
            print(f"Error: Path exists but is not a directory: {path}", file=sys.stderr)
            return False
    except PermissionError:
        print(f"Error: Permission denied creating directory: {path}", file=sys.stderr)
        return False
    except Exception as e:
        print(f"Error creating directory {path}: {e}", file=sys.stderr)
        return False

def main():
    """
    Main entry point for creating state directories.
    Creates the specific state directory structure for the project.
    """
    # Define the project root relative to this script's location
    # Assuming this script is in code/ and project root is one level up
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent
    
    # Define the specific state directory path as per task T001c
    # The path includes the project name nested under state/projects/
    state_dir_path = project_root / "state" / "projects" / "PROJ-560-embodied-curriculum-learning-physical-si"
    
    print(f"Creating state directory: {state_dir_path}")
    
    if create_directory(str(state_dir_path)):
        print(f"Successfully created state directory: {state_dir_path}")
        # Create a marker file to ensure the directory is non-empty as per verifier requirements
        marker_file = state_dir_path / ".gitkeep"
        try:
            marker_file.touch(exist_ok=True)
            print(f"Created marker file: {marker_file}")
        except Exception as e:
            print(f"Warning: Could not create marker file {marker_file}: {e}", file=sys.stderr)
        return 0
    else:
        print(f"Failed to create state directory: {state_dir_path}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())