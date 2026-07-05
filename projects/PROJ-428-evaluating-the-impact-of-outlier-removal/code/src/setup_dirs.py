"""
Setup script to create the project's data and state directory structure.

Creates the following directories atomically (using mkdir -p logic):
- data/raw/
- data/processed/
- data/results/
- data/results/figures/
- state/

Ensures idempotency by checking existence before creation.
"""
import os
import sys
from pathlib import Path

def setup_directories(root_dir: str) -> None:
    """
    Create the required directory structure under the given root directory.
    
    Args:
        root_dir: The project root directory path (e.g., 'projects/PROJ-428-...').
    """
    root = Path(root_dir).resolve()
    
    required_dirs = [
        root / "data" / "raw",
        root / "data" / "processed",
        root / "data" / "results",
        root / "data" / "results" / "figures",
        root / "state",
    ]
    
    created_count = 0
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory exists: {dir_path}")
    
    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} new directories.")

if __name__ == "__main__":
    # Default to current working directory if no argument provided
    project_root = sys.argv[1] if len(sys.argv) > 1 else "."
    setup_directories(project_root)
    print("Directory setup complete.")