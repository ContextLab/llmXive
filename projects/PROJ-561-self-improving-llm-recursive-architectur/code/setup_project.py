"""
Project Structure Initialization Script.
Creates the directory hierarchy and __init__.py files as defined in T001.
"""
import os
import sys
from pathlib import Path

def create_project_structure():
    """
    Creates the required project directories and initializes __init__.py files.
    """
    # Define the root directory (parent of this script's directory if in code/, or current)
    # We assume this script is run from the project root or code/ root.
    # Based on the task, we need to create these relative to the project root.
    # Let's assume we are running from the project root, or we derive it.
    
    # If running as `python code/setup_project.py`, we need to go up one level or stay relative.
    # The task specifies paths like `code/`, `data/raw/`.
    # We will assume the script is run from the project root.
    
    base_path = Path.cwd()
    
    # If the script is located in code/, adjust base_path if necessary.
    # But typically, project structure scripts are run from root.
    # Let's define the directories relative to the current working directory.
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "specs",
        "tests",
        "tests/unit",
        "tests/integration"
    ]
    
    # Check if we are already inside 'code' and adjust if needed to avoid double nesting
    # But the task says "Create directories code/...".
    # We will create them relative to the current working directory.
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
        
        # Create __init__.py in the leaf directories of the new structure
        # The task asks to initialize __init__.py files.
        # We should add them to the directories we create or ensure they exist.
        # Specifically for: code/, data/raw, data/processed, results, specs, tests, tests/unit, tests/integration
        
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created __init__.py: {init_file}")
            created_count += 1
        else:
            print(f"__init__.py already exists: {init_file}")
    
    print(f"Project structure setup complete. Created {created_count} new items.")

if __name__ == "__main__":
    create_project_structure()
