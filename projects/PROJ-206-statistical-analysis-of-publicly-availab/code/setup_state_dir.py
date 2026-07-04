import os
import sys
from pathlib import Path

def main():
    """
    Create the 'state' directory at the project root.
    
    This directory is used to store project state files, including
    checksums, execution logs, and intermediate workflow states.
    """
    project_root = Path(__file__).resolve().parent
    state_dir = project_root / "state"
    
    if not state_dir.exists():
        state_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {state_dir}")
    else:
        print(f"Directory already exists: {state_dir}")
    
    # Create subdirectories for organization
    projects_dir = state_dir / "projects"
    if not projects_dir.exists():
        projects_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created subdirectory: {projects_dir}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
