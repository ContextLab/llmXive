import os
from pathlib import Path

def create_project_structure():
    """
    Create the project directory structure as specified in T001.
    This function ensures all required directories exist.
    """
    # Define the directories to create relative to the project root
    # Assuming this script is run from the project root or code/ directory
    # We use the current working directory as the root for safety
    base_dir = Path.cwd()
    
    directories = [
        "code/data",
        "code/analysis",
        "code/viz",
        "code/tests",
        "artifacts/figures",
        "artifacts/reports",
        "state"
    ]
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # print(f"Created directory: {full_path}")
    
    return True

if __name__ == "__main__":
    create_project_structure()
    print("Project structure created successfully.")