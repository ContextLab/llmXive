import os
from pathlib import Path

def create_project_structure():
    """
    Creates the root directory structure for the project under:
    projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code/
    
    This function ensures the existence of the base project code directory
    and returns the path to the root code directory.
    """
    project_root = Path("projects/PROJ-951-llmxive-follow-up-extending-physisforcin/code")
    
    # Ensure the directory exists
    project_root.mkdir(parents=True, exist_ok=True)
    
    print(f"Project root created at: {project_root.resolve()}")
    return project_root

if __name__ == "__main__":
    create_project_structure()
