"""
Directory setup module for the llmXive automated science pipeline.

This module handles the creation of the project directory structure
as defined in the plan.md and tasks.md specifications.

It ensures that all required directories for data storage (raw, processed,
generated, validation), code modules, and tests exist before any other
pipeline components are executed.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """
    Create the standard project directory tree.
    
    This function creates the following directory structure relative
    to the project root:
    
    - code/
    - data/raw/
    - data/processed/
    - data/generated/
    - data/validation/
    - tests/
    
    It is idempotent; calling it multiple times will not raise errors
    if the directories already exist.
    
    Returns:
        bool: True if all directories were successfully created or already exist.
        
    Raises:
        OSError: If there is a permission error or disk space issue preventing
                 directory creation.
    """
    # Determine the project root. 
    # We assume this script is located in 'code/', so root is parent of code/.
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    # Define the relative paths to create
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/generated",
        "data/validation",
        "tests"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                created_count += 1
            except OSError as e:
                print(f"Error creating directory {full_path}: {e}", file=sys.stderr)
                return False
        else:
            # Verify it is actually a directory, not a file
            if not full_path.is_dir():
                print(f"Path exists but is not a directory: {full_path}", file=sys.stderr)
                return False
    
    print(f"Directory setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    success = create_directories()
    sys.exit(0 if success else 1)
