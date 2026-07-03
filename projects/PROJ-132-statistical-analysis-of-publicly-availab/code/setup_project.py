import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the project directory structure as defined in the implementation plan.
    
    Creates the following directories relative to the project root:
    - src/data, src/models, src/analysis
    - data/raw, data/processed, data/interim
    - tests/contract, tests/unit, tests/integration
    - docs
    """
    # Define the directory structure relative to the project root
    # The project root is assumed to be the parent of 'code/' or we run from root
    # Based on task description, paths are relative to project root.
    # We assume this script is run from the project root or code/ is a subfolder.
    # The task asks to create structure "per implementation plan".
    # The plan implies a standard layout. We will create these relative to the current working directory.
    
    base_dirs = [
        "src/data",
        "src/models",
        "src/analysis",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "docs"
    ]
    
    created_count = 0
    for dir_path in base_dirs:
        full_path = Path(dir_path)
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        except PermissionError:
            print(f"Permission denied creating directory: {full_path}", file=sys.stderr)
        except Exception as e:
            print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
    
    print(f"Project structure setup complete. {created_count} directories created/verified.")
    return created_count

if __name__ == "__main__":
    create_directories()