import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the project directory structure as defined in tasks.md T001.
    Directories created:
    - src/
    - tests/
    - data/
    - data/raw/
    - data/processed/
    - data/results/
    - state/
    
    Also creates __init__.py files to ensure Python package recognition.
    """
    # Define the project root (current working directory or explicit path)
    # Assuming this script runs from the project root
    project_root = Path.cwd()
    
    # Define the relative paths to create
    directories = [
        "src",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "data/logs",  # Added based on usage in download.py and T013
        "state",
        "contracts",  # Required for schema contracts (T007a, T008a, etc.)
        "figures",    # Required for output plots (T032)
    ]
    
    created_dirs = []
    skipped_dirs = []
    
    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            
            # Create __init__.py for Python packages
            if dir_path.startswith("src") or dir_path.startswith("tests"):
                init_file = full_path / "__init__.py"
                if not init_file.exists():
                    init_file.write_text("# Auto-generated init file\n")
        except Exception as e:
            print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
    
    # Create .gitkeep files for empty data directories to ensure they are tracked by git
    data_dirs = ["data/raw", "data/processed", "data/results", "data/logs"]
    for dir_path in data_dirs:
        full_path = project_root / dir_path
        keep_file = full_path / ".gitkeep"
        if not keep_file.exists():
            keep_file.write_text("")
            if str(full_path) not in created_dirs:
                created_dirs.append(str(full_path))
    
    print(f"Project structure created successfully at: {project_root}")
    print(f"Directories created: {len(created_dirs)}")
    for d in created_dirs:
        print(f"  - {d}")
        
    return True

if __name__ == "__main__":
    create_structure()
