import os
import sys
from pathlib import Path

def main():
    """
    Create the required directory structure for the project.
    This script ensures that the following directories exist relative to the project root:
    - code/
    - data/raw/
    - data/processed/
    - tests/
    - contracts/
    """
    # Determine project root. Assuming this script is run from the project root or
    # the project root is the parent of 'code'.
    # We try to resolve the project root by looking for the 'projects' directory structure
    # or simply assuming the current working directory is the project root for T001b context.
    # Based on T001a, the root is `projects/PROJ-160-investigating-the-impact-of-early-life-s/`.
    
    # If run as `python code/setup.py` from the project root:
    project_root = Path.cwd()
    
    # If the script is located in `code/`, we might need to adjust if run from elsewhere,
    # but typically for setup scripts, we assume execution from root.
    # To be safe, we check if we are inside `code/` and adjust if necessary, 
    # but the prompt implies we are setting up the root structure.
    
    # Let's verify we are in the correct project directory.
    # The task specifies creating dirs INSIDE `projects/PROJ-160-investigating-the-impact-of-early-life-s/`.
    # If `project_root` matches that name or is the parent of `code`, we proceed.
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "contracts"
    ]
    
    created = []
    skipped = []
    
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created.append(str(dir_path))
        else:
            skipped.append(str(dir_path))
    
    print(f"Project Root: {project_root}")
    print(f"Created directories: {created}")
    print(f"Skipped (already exist): {skipped}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())