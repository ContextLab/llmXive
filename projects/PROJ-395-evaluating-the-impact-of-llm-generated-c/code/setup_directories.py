"""
Directory setup utility for the llmXive project.
Creates the required directory structure for data, code, state, and tests.
"""
import os
import sys
from pathlib import Path

def main() -> None:
    """
    Creates the required directory structure for the project.
    Specifically creates:
    - data/raw/
    - data/processed/
    - state/
    - code/ (if not already present at root, though typically code/ is the root for modules)
    
    This script is idempotent; it will not fail if directories already exist.
    """
    # Determine the project root. 
    # Based on tasks.md and standard structure, we assume this script is run from the project root.
    # The task requires: data/raw/, data/processed/, state/, and code/ directories.
    
    project_root = Path.cwd()
    
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "state",
        # code/ is usually where this script lives, but we ensure it exists relative to root if needed.
        # However, the task specifically asks for "Setup ... directories". 
        # If this script is in code/, creating code/ at root might be redundant or create a nested code/code.
        # Assuming the project root is the parent of 'code', we create 'code' at root if missing.
        # But typically, for a script in code/, the 'code' directory is the current directory.
        # Let's create it relative to cwd to be safe, assuming cwd is the project root.
        project_root / "code",
    ]
    
    created_count = 0
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    if created_count == 0:
        print("All required directories already exist.")
    else:
        print(f"Successfully created {created_count} directory/directories.")

if __name__ == "__main__":
    main()