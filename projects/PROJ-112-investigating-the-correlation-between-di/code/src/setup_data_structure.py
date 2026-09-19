import os
from pathlib import Path
import sys

def get_project_root() -> Path:
    """
    Determines the project root directory.
    Assumes the script is run from the repository root or 'code' directory.
    """
    current_path = Path(__file__).resolve()
    # If running from code/src/setup_data_structure.py, go up 3 levels to repo root
    # If running from code/setup_data_structure.py, go up 2 levels
    # We check for a marker file or standard structure to be robust.
    # Assuming standard layout: repo_root/code/src/... or repo_root/code/...
    
    # Strategy: Look for 'data' directory at current level or parent levels
    # or check for 'requirements.txt' or 'README.md'
    
    # Try starting from script location
    candidate = current_path.parent.parent # code/src -> code -> repo_root
    
    if (candidate / "requirements.txt").exists():
        return candidate
    
    # Fallback: check parent
    candidate = candidate.parent
    if (candidate / "requirements.txt").exists():
        return candidate
        
    # If we can't find it, assume current working directory is root
    return Path.cwd()

def setup_directories() -> None:
    """
    Creates the required data directory structure as per T008:
    - data/raw/
    - data/processed/
    - data/processed/results/
    
    Also ensures 'state/' exists if not present (often needed for checksums).
    """
    root = get_project_root()
    data_root = root / "data"
    raw_dir = data_root / "raw"
    processed_dir = data_root / "processed"
    results_dir = processed_dir / "results"
    state_dir = root / "state"
    
    dirs_to_create = [raw_dir, processed_dir, results_dir, state_dir]
    
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        else:
            print(f"Directory already exists: {dir_path}")

def main() -> None:
    """
    Entry point for the data structure setup script.
    """
    setup_directories()
    print("Data directory structure setup complete.")

if __name__ == "__main__":
    main()