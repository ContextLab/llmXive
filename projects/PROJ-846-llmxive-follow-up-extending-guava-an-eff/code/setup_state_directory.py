import os
import sys
from pathlib import Path

def create_state_directory() -> Path:
    """
    Create the 'state/' directory in the repository root if it does not exist.
    
    Returns:
        Path: The absolute path to the created (or existing) state directory.
    
    Raises:
        RuntimeError: If the directory cannot be created due to permissions or other OS errors.
    """
    repo_root = Path.cwd()
    state_dir = repo_root / "state"
    
    if not state_dir.exists():
        try:
            state_dir.mkdir(parents=True, exist_ok=True)
            # Create a .gitkeep to ensure the directory is tracked by git
            gitkeep = state_dir / ".gitkeep"
            gitkeep.touch(exist_ok=True)
        except OSError as e:
            raise RuntimeError(f"Failed to create state directory at {state_dir}: {e}")
    
    return state_dir

def main() -> int:
    """
    Entry point for the script. Creates the state directory and verifies its existence.
    
    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    try:
        state_dir = create_state_directory()
        print(f"State directory created/verified at: {state_dir}")
        
        # Verification: Ensure the directory exists
        if not state_dir.is_dir():
            print(f"ERROR: Verification failed. {state_dir} is not a directory.")
            return 1
        
        print("Verification successful: state/ directory exists.")
        return 0
        
    except Exception as e:
        print(f"ERROR: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
