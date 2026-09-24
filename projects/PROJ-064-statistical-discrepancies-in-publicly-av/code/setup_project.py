import os
import sys
from pathlib import Path

def initialize_project_structure():
    """
    Initialize the project directory structure for PROJ-064.
    Creates the root project folder and all required subdirectories
    in a single atomic step.
    
    Structure created:
    projects/PROJ-064-statistical-discrepancies-in-publicly-av/
    ├── code/
    ├── data/
    │   ├── raw/
    │   └── processed/
    ├── tests/
    ├── docs/
    ├── state/
    └── config/
    """
    # Define the project root relative to the current working directory
    # Assuming this script is run from the project root or a parent context
    # We create it relative to the current directory where the script is invoked
    project_name = "PROJ-064-statistical-discrepancies-in-publicly-av"
    base_path = Path(".") / "projects" / project_name
    
    # Define required directories
    directories = [
        base_path / "code",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "tests",
        base_path / "docs",
        base_path / "state",
        base_path / "config",
    ]
    
    # Create directories atomically (all or nothing conceptually, though os.makedirs is individual)
    # We check existence first to avoid errors if partial run occurred
    missing = []
    for dir_path in directories:
        if not dir_path.exists():
            missing.append(dir_path)
    
    if missing:
        print(f"Creating {len(missing)} directories for {project_name}...")
        for dir_path in missing:
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {dir_path}")
        print(f"Successfully initialized project structure at: {base_path}")
    else:
        print(f"Project structure at {base_path} already exists.")
    
    return base_path

if __name__ == "__main__":
    initialize_project_structure()
