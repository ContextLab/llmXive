"""
Setup script to create the 'state/' directory in the repository root.

This script implements Task T005a:
- Creates `state/` directory in repository root.
- Verifies the directory exists after creation.

Usage:
    python code/setup_state_directory.py
"""
import os
import sys
from pathlib import Path

def create_state_directory() -> Path:
    """
    Creates the 'state/' directory in the repository root if it does not exist.
    
    Returns:
        Path: The absolute path to the created/existing state directory.
        
    Raises:
        RuntimeError: If the directory cannot be created or verified.
    """
    # Determine repository root (parent of 'code/')
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    repo_root = code_dir.parent

    state_dir = repo_root / "state"

    if state_dir.exists():
        if state_dir.is_dir():
            print(f"State directory already exists: {state_dir}")
            return state_dir
        else:
            raise RuntimeError(f"Path exists but is not a directory: {state_dir}")

    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        print(f"Successfully created state directory: {state_dir}")
    except OSError as e:
        raise RuntimeError(f"Failed to create state directory {state_dir}: {e}")

    # Verification step
    if not state_dir.exists() or not state_dir.is_dir():
        raise RuntimeError(f"Verification failed: State directory {state_dir} was not created successfully.")

    return state_dir

def main():
    """Entry point for the script."""
    try:
        state_path = create_state_directory()
        print(f"Verification: Directory '{state_path}' exists and is valid.")
        # List contents to prove existence (empty or not)
        contents = list(state_path.iterdir())
        if not contents:
            print("Directory is empty (as expected for initial creation).")
        else:
            print(f"Directory contents: {[p.name for p in contents]}")
        return 0
    except RuntimeError as e:
        print(f"Error: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())