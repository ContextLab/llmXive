import os
import sys
from pathlib import Path
from typing import List

def setup_data_directories(base_dir: Path) -> List[Path]:
    """
    Create the required data directory structure for the project.
    
    Args:
        base_dir: The root directory of the project (e.g., projects/PROJ-884-...)
    
    Returns:
        A list of created Path objects.
    """
    # Define the relative paths required for T004
    # Per task description: data/raw/ for immutable puzzles, data/processed/ for logs/results
    relative_paths = [
        "data/raw",
        "data/processed"
    ]
    
    created_dirs = []
    for rel_path in relative_paths:
        target_path = base_dir / rel_path
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(target_path)
        else:
            # Ensure it is actually a directory, not a file
            if not target_path.is_dir():
                raise NotADirectoryError(f"Path exists but is not a directory: {target_path}")
            created_dirs.append(target_path)
    
    return created_dirs

def main():
    """
    Entry point for running the directory setup script.
    Assumes the script is run from the project root or a parent directory
    where the specific project folder exists or needs to be created.
    """
    # Determine the base project directory based on the task context.
    # The task is part of project PROJ-884-llmxive-follow-up-extending-self-improvi
    # We look for the current working directory if it matches the pattern, 
    # or we assume the script is run from the project root.
    
    cwd = Path.cwd()
    
    # Check if we are already in the project root
    if cwd.name == "PROJ-884-llmxive-follow-up-extending-self-improvi":
        base_dir = cwd
    else:
        # Fallback: assume the script is run from the project root
        base_dir = cwd
        
        # Safety check: ensure we are not running from the repo root accidentally
        # by checking for the presence of 'code' or 'data' directories
        if not (base_dir / "code").exists() and not (base_dir / "data").exists():
            print(f"Warning: Current directory {base_dir} does not contain 'code' or 'data'.")
            print("Creating data directories in current directory.")

    print(f"Setting up data directories in: {base_dir}")
    
    try:
        created = setup_data_directories(base_dir)
        print(f"Successfully created/verified {len(created)} directories:")
        for d in created:
            print(f"  - {d}")
    except Exception as e:
        print(f"Error setting up data directories: {e}", file=sys.stderr)
        sys.exit(1)

if __name__ == "__main__":
    main()