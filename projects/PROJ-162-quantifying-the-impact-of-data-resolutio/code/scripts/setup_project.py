import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure as specified in the implementation plan.
    Creates: src, tests, data/raw, data/processed, data/profiling, contracts, state.
    """
    # Determine project root (assume script is at code/scripts/setup_project.py)
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent
    
    # Define relative paths to create
    directories = [
        "src",
        "tests",
        "data/raw",
        "data/processed",
        "data/profiling",
        "contracts",
        "state"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            # Ensure it is a directory
            if dir_path.is_dir():
                print(f"Directory exists: {dir_path}")
            else:
                raise RuntimeError(f"Path exists but is not a directory: {dir_path}")
    
    print(f"Project structure setup complete. Created {created_count} new directories.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
