"""
Project initialization module for llmXive pipeline.
Handles the creation of the standard directory structure.
"""
import os
from pathlib import Path


def initialize_project_structure() -> None:
    """
    Creates the required project directory structure.
    
    Creates the following directories relative to the project root:
    - code/
    - tests/
    - data/raw/
    - data/processed/
    - results/
    
    This function is idempotent; it will not raise errors if directories
    already exist.
    """
    # Define the base project root (assuming this script is in code/, go up one level)
    # However, to be safe and flexible, we assume the current working directory
    # is the project root when this is executed, or we define relative paths explicitly.
    # The safest approach for a setup script is to create relative paths from cwd.
    
    base_path = Path.cwd()
    
    directories = [
        "code",
        "tests",
        "data/raw",
        "data/processed",
        "results"
    ]
    
    created_count = 0
    existing_count = 0
    
    for dir_name in directories:
        dir_path = base_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {dir_path}")
        else:
            existing_count += 1
            print(f"Directory already exists: {dir_path}")
    
    print(f"Project structure initialization complete. "
          f"Created: {created_count}, Existing: {existing_count}")
