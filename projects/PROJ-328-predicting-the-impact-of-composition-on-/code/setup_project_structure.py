import os
import sys
from pathlib import Path

def main():
    """
    Create the project directory structure for PROJ-328.
    
    Creates the following directories relative to the project root:
    - projects/PROJ-328-predicting-the-impact-of-composition-on-/data/
    - projects/PROJ-328-predicting-the-impact-of-composition-on-/code/
    - projects/PROJ-328-predicting-the-impact-of-composition-on-/tests/
    - projects/PROJ-328-predicting-the-impact-of-composition-on-/models/
    """
    # Determine project root (assuming script is run from root or code/)
    # We look for the specific project directory path as defined in tasks.md
    project_name = "PROJ-328-predicting-the-impact-of-composition-on-"
    
    # If running from code/, we need to go up one level to find the project root
    current_path = Path.cwd()
    
    # Check if we are already inside the project directory
    if current_path.name == project_name:
        project_root = current_path
    else:
        # Assume project is a subdirectory of the current working directory
        project_root = current_path / project_name
    
    # Define the required subdirectories
    required_dirs = [
        "data",
        "code",
        "tests",
        "models"
    ]
    
    print(f"Setting up project structure for: {project_name}")
    print(f"Target root: {project_root}")
    
    created_count = 0
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"Project setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    sys.exit(main())