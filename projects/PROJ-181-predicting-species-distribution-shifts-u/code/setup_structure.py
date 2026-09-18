import os
import sys
from pathlib import Path

def main():
    """
    Initialize the project directory structure for PROJ-181.
    Creates the root project folder and all required subdirectories.
    """
    # Define the project root relative to the script location or current working directory
    # The task specifies the project is at projects/PROJ-181-predicting-species-distribution-shifts-u/
    project_root = Path("projects/PROJ-181-predicting-species-distribution-shifts-u")
    
    # Define the directory structure to create
    directories = [
        "code",
        "data",
        "tests",
        "metrics",
        "reports",
        "logs",
        "state",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "tests/unit",
        "tests/integration",
        "contracts"
    ]
    
    print(f"Initializing project structure at: {project_root.absolute()}")
    
    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {full_path}")
        except OSError as e:
            print(f"  Error creating {full_path}: {e}")
            sys.exit(1)
    
    # Create a .gitkeep file in each directory to ensure they are tracked by git
    # This is a common practice for empty directories in version control
    for dir_path in directories:
        full_path = project_root / dir_path / ".gitkeep"
        try:
            full_path.touch(exist_ok=True)
        except OSError as e:
            print(f"  Warning: Could not create .gitkeep in {full_path}: {e}")
    
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()