import os
import sys
from pathlib import Path

def create_project_structure():
    """
    Creates the project directory structure for PROJ-317.
    
    This function creates the following directories relative to the project root:
    - data/stimuli
    - data/stimuli_metadata
    - data/responses
    - data/processed
    - data/ethics
    - code/data
    - code/stimuli
    - code/participants
    - code/analysis
    - tests/unit
    - tests/integration
    - tests/contract
    - docs/ethics
    """
    # Determine the project root. 
    # We assume this script is run from the project root or a subdirectory within it.
    # To be robust, we look for a specific marker or just use the current working directory
    # if the paths are relative to where the script is invoked.
    # Based on the task description, paths are relative to the project root.
    # We will assume the script is run from the project root.
    
    project_root = Path.cwd()
    
    directories = [
        "data/stimuli",
        "data/stimuli_metadata",
        "data/responses",
        "data/processed",
        "data/ethics",
        "code/data",
        "code/stimuli",
        "code/participants",
        "code/analysis",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "docs/ethics"
    ]
    
    created_dirs = []
    skipped_dirs = []
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
        else:
            skipped_dirs.append(str(full_path))
    
    print(f"Project structure created in: {project_root}")
    print(f"Created {len(created_dirs)} directories:")
    for d in created_dirs:
        print(f"  - {d}")
    
    if skipped_dirs:
        print(f"Skipped {len(skipped_dirs)} existing directories:")
        for d in skipped_dirs:
            print(f"  - {d}")
    
    return True

if __name__ == "__main__":
    create_project_structure()
