import os
import sys
from pathlib import Path

def main():
    """
    Creates the 'state/' directory at the project root if it does not exist.
    This directory is used for storing project state files, hashes, and metadata.
    """
    # Determine project root (assuming this script is in code/ relative to root)
    # Or we can use a standard relative path if run from root.
    # To be robust, we check if we are running from the repo root or code/ subdir.
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    state_dir = project_root / "state"

    if not state_dir.exists():
        state_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created state directory: {state_dir}")
    else:
        print(f"State directory already exists: {state_dir}")

    # Create a .gitkeep file to ensure the directory is tracked by git
    gitkeep = state_dir / ".gitkeep"
    if not gitkeep.exists():
        gitkeep.touch()
        print(f"Created .gitkeep in: {gitkeep}")

    return 0

if __name__ == "__main__":
    sys.exit(main())
