import os
import sys
from pathlib import Path

def setup_directories():
    """
    Creates the required directory structure for the llmXive project.
    
    Creates the following directories relative to the project root:
    - data/raw
    - data/processed
    - data/interim
    - data/results
    - code/
    - tests/
    
    Returns:
        bool: True if all directories were created or already exist, False on error.
    """
    # Determine project root (assuming this script is run from project root or code/)
    # We look for the 'projects' directory structure or just use the current working directory
    # based on the task requirement to live under the project tree.
    
    # If running from code/, go up one level
    current_dir = Path.cwd()
    if current_dir.name == 'code':
        project_root = current_dir.parent
    else:
        project_root = current_dir

    # Define the required subdirectories relative to project root
    required_dirs = [
        project_root / 'data' / 'raw',
        project_root / 'data' / 'processed',
        project_root / 'data' / 'interim',
        project_root / 'data' / 'results',
        project_root / 'code',
        project_root / 'tests',
    ]

    success = True
    for dir_path in required_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created or verified directory: {dir_path}")
        except OSError as e:
            print(f"Error creating directory {dir_path}: {e}", file=sys.stderr)
            success = False

    return success

if __name__ == "__main__":
    success = setup_directories()
    sys.exit(0 if success else 1)
