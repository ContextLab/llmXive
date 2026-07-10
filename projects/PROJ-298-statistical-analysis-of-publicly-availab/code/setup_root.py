"""
T001a: Create the root directory for project PROJ-298.

This script ensures the existence of the project root directory
and creates the initial subdirectory structure required for the
llmXive pipeline (code, data, tests, notebooks, specs).

It is idempotent: running it multiple times will not fail if
the directories already exist.
"""
import os
from pathlib import Path

# Define the project root relative to the script location or current working dir
# The task requires the directory to be at projects/PROJ-298-statistical-analysis-of-publicly-availab/
# We will resolve this relative to the current working directory (CWD) where the script is run.

PROJECT_ROOT_NAME = "PROJ-298-statistical-analysis-of-publicly-availab"
PROJECTS_PARENT = "projects"

# Subdirectories to ensure exist under the project root
REQUIRED_DIRS = [
    "code",
    "data",
    "tests",
    "notebooks",
    "specs",
    "figures",
    "state"
]

def main():
    # Construct the full path
    # We assume the script is run from the repository root
    root_path = Path(PROJECTS_PARENT) / PROJECT_ROOT_NAME
    
    print(f"Ensuring existence of project root: {root_path}")
    
    if not root_path.exists():
        root_path.mkdir(parents=True, exist_ok=True)
        print(f"Created project root directory: {root_path}")
    else:
        print(f"Project root directory already exists: {root_path}")
    
    # Create subdirectories
    created_count = 0
    for dir_name in REQUIRED_DIRS:
        dir_path = root_path / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"  Created: {dir_path}")
            created_count += 1
        else:
            print(f"  Exists: {dir_path}")
    
    print(f"Directory setup complete. {created_count} new directories created.")
    return 0

if __name__ == "__main__":
    exit(main())