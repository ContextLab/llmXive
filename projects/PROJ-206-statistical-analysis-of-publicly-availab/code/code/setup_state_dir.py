import os
import sys
from pathlib import Path

def main():
    """
    Creates the 'state' directory at the project root if it does not exist.
    This directory is used for storing project state files, hashes, and metadata.
    """
    # Determine project root (assuming this script is at code/setup_state_dir.py)
    # We need to go up two levels to reach the repository root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent

    state_dir = project_root / "state"

    if not state_dir.exists():
        state_dir.mkdir(parents=True)
        print(f"Created state directory: {state_dir}")
    else:
        print(f"State directory already exists: {state_dir}")

    # Ensure the directory is non-empty by creating a .gitkeep file
    # This ensures the directory is tracked by git even if empty
    gitkeep_file = state_dir / ".gitkeep"
    if not gitkeep_file.exists():
        gitkeep_file.write_text("# State directory for project artifacts\n")
        print(f"Created .gitkeep in state directory: {gitkeep_file}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
