import os
from pathlib import Path

def create_structure(project_name: str = "PROJ-558-consciousness-bootstrapping-self-aware-a") -> None:
    """
    Creates the directory structure for the project as specified in T001a.
    
    Structure:
    projects/{project_name}/
    ├── data/raw
    ├── data/processed
    ├── code
    ├── tests
    ├── artifacts
    ├── artifacts/checkpoints
    └── artifacts/results
    
    Args:
        project_name: The name of the project directory to create under 'projects/'.
    """
    base_dir = Path("projects")
    project_dir = base_dir / project_name
    
    # Define subdirectories relative to the project root
    subdirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "artifacts",
        "artifacts/checkpoints",
        "artifacts/results",
    ]
    
    # Create the project root directory if it doesn't exist
    project_dir.mkdir(parents=True, exist_ok=True)
    print(f"Created project directory: {project_dir}")
    
    # Create all subdirectories
    for subdir in subdirs:
        dir_path = project_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"  Created: {dir_path}")
    
    print(f"Directory structure for '{project_name}' created successfully.")

if __name__ == "__main__":
    create_structure()
