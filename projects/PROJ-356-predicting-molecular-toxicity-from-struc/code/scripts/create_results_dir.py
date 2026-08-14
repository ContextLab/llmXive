import os
from pathlib import Path

def main():
    """Create the results directory for the project."""
    # The project root is assumed to be the parent of the 'code' directory
    # based on the task description path: projects/PROJ-356-.../code/results/
    # We calculate this relative to the script's location or the provided structure.
    
    # Assuming standard project layout where this script runs from the repo root
    # or the 'code' directory.
    current_dir = Path(__file__).parent
    project_root = current_dir.parent # code/
    results_dir = project_root / "results"
    
    if not results_dir.exists():
        results_dir.mkdir(parents=True, exist_ok=True)
        print(f"Created results directory: {results_dir}")
    else:
        print(f"Results directory already exists: {results_dir}")

    return results_dir

if __name__ == "__main__":
    main()