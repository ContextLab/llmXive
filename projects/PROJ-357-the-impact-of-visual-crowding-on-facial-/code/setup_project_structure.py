"""
Project Setup Script for PROJ-357-the-impact-of-visual-crowding-on-facial-

This script creates the required directory structure for the project:
- code/
- data/
- tests/
- artifacts/
- state/projects/
"""

import os
from pathlib import Path

def setup_project_structure():
    """
    Creates the root project directory and all required subdirectories.
    
    Returns:
        bool: True if successful, False otherwise.
    """
    # Define the project root directory
    project_root = Path("projects/PROJ-357-the-impact-of-visual-crowding-on-facial-")
    
    # Define required subdirectories
    required_dirs = [
        "code",
        "data",
        "tests",
        "artifacts",
        "state/projects"
    ]
    
    try:
        # Create the project root directory
        project_root.mkdir(parents=True, exist_ok=True)
        print(f"Created project root: {project_root}")
        
        # Create each required subdirectory
        for dir_name in required_dirs:
            dir_path = project_root / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        
        # Create additional standard subdirectories for organization
        additional_dirs = [
            "data/raw",
            "data/interim",
            "data/processed",
            "code/utils",
            "code/analysis",
            "tests/unit",
            "tests/integration",
            "figures"
        ]
        
        for dir_name in additional_dirs:
            dir_path = project_root / dir_name
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
        
        print(f"\nProject structure successfully created at: {project_root}")
        return True
        
    except Exception as e:
        print(f"Error creating project structure: {e}")
        return False


if __name__ == "__main__":
    success = setup_project_structure()
    if not success:
        exit(1)