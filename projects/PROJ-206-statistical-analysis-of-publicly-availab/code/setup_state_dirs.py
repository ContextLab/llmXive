import os
import sys
from pathlib import Path

def main():
    """
    Create the 'state/' directory at the project root.
    This directory is used to store project state manifests,
    artifact hashes, and execution logs.
    """
    # Determine project root relative to this script location
    # Assuming script is at code/setup_state_dirs.py, root is parent of 'code'
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    state_dir = project_root / "state"

    if state_dir.exists():
        print(f"Directory already exists: {state_dir}")
        return 0

    try:
        state_dir.mkdir(parents=True, exist_ok=True)
        print(f"Successfully created directory: {state_dir}")
        
        # Create a .gitkeep file to ensure the directory is tracked by git
        # even if it is initially empty, as per standard practice.
        gitkeep = state_dir / ".gitkeep"
        gitkeep.write_text("# State directory for project artifacts and manifests\n")
        print(f"Created placeholder file: {gitkeep}")
        
        return 0
    except OSError as e:
        print(f"Error creating directory {state_dir}: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())