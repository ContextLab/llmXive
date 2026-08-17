"""
Script to initialize the project directory structure for PROJ-743.
Creates the required directories as per the implementation plan.
"""
import os
import sys
from pathlib import Path

def ensure_directories():
    """
    Creates the necessary project directories.
    Returns a list of created paths.
    """
    # Base directory is the project root (where this script is run from)
    # We assume the script is run from the project root.
    # If not, we can derive it from __file__ if needed, but typically
    # these scripts are executed from the root.
    
    # Define relative paths based on the task description
    # The task specifies: code/, data/raw/, data/processed/, results/figures/, 
    # results/logs/, results/stats/, tests/
    
    # Note: 'code/' and 'tests/' are typically created alongside this script,
    # but we ensure them explicitly to be safe.
    # 'results/' is a parent for figures, logs, stats.
    
    relative_paths = [
        "code",
        "data/raw",
        "data/processed",
        "results/figures",
        "results/logs",
        "results/stats",
        "tests"
    ]
    
    created_dirs = []
    for rel_path in relative_paths:
        target = Path(rel_path)
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(target))
            print(f"Created directory: {target}")
        else:
            # Even if it exists, we consider it 'ensured'
            created_dirs.append(str(target))
            
    return created_dirs

def main():
    """Entry point for the script."""
    print("Initializing project structure for PROJ-743...")
    dirs = ensure_directories()
    print(f"Project structure initialized. Ensured {len(dirs)} directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
