import os
import sys
from pathlib import Path

def create_directories():
    """
    Creates the standard project directory structure for llmXive PROJ-331.
    
    Directories created relative to the project root:
    - code/
    - tests/
    - data/raw/
    - data/processed/
    - data/logs/
    - results/
    - state/
    
    Returns:
        list: A list of absolute paths to the created directories.
    """
    # Define relative paths based on project requirements
    relative_paths = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "data/logs",
        "results",
        "state"
    ]

    # Determine project root (parent of the code directory)
    # Assuming this script is run from the project root or code/
    current_file = Path(__file__).resolve()
    # Try to find project root by looking for a specific marker or just use parent of code/
    # For robustness, we assume the script is in code/ and root is parent
    project_root = current_file.parent.parent if current_file.name == "setup_project.py" else current_file.parent
    
    created_dirs = []
    
    for rel_path in relative_paths:
        dir_path = project_root / rel_path
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
            print(f"Created directory: {dir_path}")
        except PermissionError:
            print(f"Error: Permission denied creating directory: {dir_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
    
    return created_dirs

if __name__ == "__main__":
    print("Initializing project directory structure...")
    dirs = create_directories()
    if dirs:
        print(f"Successfully created {len(dirs)} directories.")
        print("Structure ready.")
    else:
        print("No directories were created. Check permissions or paths.")
        sys.exit(1)
