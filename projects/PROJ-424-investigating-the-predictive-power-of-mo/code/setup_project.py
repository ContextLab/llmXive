import os
import sys
from pathlib import Path

def create_directory_structure():
    """
    Creates the required project directory structure for PROJ-424.
    Directories created relative to the project root:
    - code/
    - data/raw/
    - data/processed/
    - data/interim/
    - tests/unit/
    - tests/integration/
    """
    # Determine the project root. 
    # We assume the script is run from the project root or the code directory.
    # To be safe, we resolve relative to the script's location if it's in 'code',
    # otherwise relative to current working directory.
    script_path = Path(__file__).resolve()
    if script_path.name == 'setup_project.py':
        # If run directly, assume current directory is project root
        root = Path.cwd()
    else:
        # If imported, try to find root relative to 'code' folder
        code_dir = script_path.parent
        if code_dir.name == 'code':
            root = code_dir.parent
        else:
            root = Path.cwd()
    
    # Define relative paths
    dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/unit",
        "tests/integration"
    ]
    
    created_count = 0
    for d in dirs:
        target = root / d
        if not target.exists():
            target.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {target}")
            created_count += 1
        else:
            print(f"Directory already exists: {target}")
    
    return created_count

def main():
    count = create_directory_structure()
    print(f"Setup complete. {count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
