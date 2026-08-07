"""
Setup script for T001g: Create the 'state' directory.
This script ensures the directory structure required for project state management exists.
"""
import os
import sys
from pathlib import Path

def create_state_directory(project_root: Path) -> Path:
    """
    Creates the 'state' directory within the project root if it does not exist.

    Args:
        project_root: The root path of the project (e.g., .../PROJ-756-...)

    Returns:
        The Path object for the created/existing state directory.
    """
    state_dir = project_root / "state"
    if not state_dir.exists():
        state_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {state_dir}")
    else:
        print(f"Directory already exists: {state_dir}")
    return state_dir

def main():
    """
    Main entry point for the script.
    Determines the project root based on the known project structure and creates the state directory.
    """
    # The project root is expected to be the parent of the 'code' directory.
    # We assume this script runs from the project root or we resolve it relative to __file__.
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    # Ensure we are in the correct project context
    expected_project_name = "PROJ-756-assessing-dataset-imbalance-effects-on-m"
    if project_root.name != expected_project_name:
        # Fallback: if code is at root, project_root is current
        if code_dir.name == expected_project_name:
            project_root = code_dir
        else:
            # Try to find the project root by looking for the specific project folder name
            # This handles cases where the script might be moved
            possible_root = code_dir.parent
            if possible_root.name == expected_project_name:
                project_root = possible_root
            else:
                print(f"Warning: Could not automatically detect project root '{expected_project_name}'. "
                      f"Assuming current directory: {project_root}")

    print(f"Project root detected as: {project_root}")
    
    try:
        state_dir = create_state_directory(project_root)
        # Verify creation
        if state_dir.exists() and state_dir.is_dir():
            print(f"SUCCESS: State directory created/verified at {state_dir}")
            return 0
        else:
            print(f"ERROR: State directory creation failed or is not a directory at {state_dir}")
            return 1
    except PermissionError as e:
        print(f"ERROR: Permission denied while creating state directory: {e}")
        return 1
    except Exception as e:
        print(f"ERROR: Unexpected error during state directory creation: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
