import os
import sys
from pathlib import Path

def create_state_directory() -> Path:
    """
    Creates the 'state/' directory in the repository root if it does not exist.
    Returns the path to the created/existing directory.
    """
    # Determine repository root. Based on task context, we assume the script
    # runs from the project root or we derive it from the current working directory.
    # The task specifies creating 'state/' in repository root.
    # We assume the script is executed from the project root or we navigate up.
    # Given the project structure in tasks.md, the root is the current dir for this script.
    
    project_root = Path.cwd()
    state_dir = project_root / "state"

    if not state_dir.exists():
        state_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created state directory: {state_dir}")
    else:
        print(f"State directory already exists: {state_dir}")

    return state_dir

def main():
    """Entry point for the script."""
    try:
        state_dir = create_state_directory()
        # Verify existence as per task requirement
        if state_dir.exists() and state_dir.is_dir():
            print(f"Verification passed: {state_dir} exists.")
            sys.exit(0)
        else:
            print(f"Verification failed: {state_dir} does not exist or is not a directory.")
            sys.exit(1)
    except Exception as e:
        print(f"Error creating state directory: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()