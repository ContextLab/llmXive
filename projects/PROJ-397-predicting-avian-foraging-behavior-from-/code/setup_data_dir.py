"""
Task T001a: Initialize the data/ directory structure.

Creates the directory `projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/`
and places a `.gitkeep` file inside to ensure the directory is tracked by git.
"""
import os
import sys
from pathlib import Path

# Define the project root relative to this script's location or use a fixed relative path
# Based on the task description, the target path is:
# projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/
# Assuming this script runs from the root of the project structure or we construct the path explicitly.

# We will construct the path relative to the current working directory to be safe,
# or assume the project root is the parent of 'code'.
# The task specifies the full path: projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/

PROJECT_NAME = "PROJ-397-predicting-avian-foraging-behavior-from-"
CODE_DIR = "code"
DATA_DIR_NAME = "data"

# Construct the full path
base_path = Path("projects") / PROJECT_NAME / CODE_DIR / DATA_DIR_NAME

def main():
    print(f"Initializing data directory: {base_path}")
    
    # Create the directory (parents=True creates intermediate directories if needed)
    try:
        base_path.mkdir(parents=True, exist_ok=True)
        print(f"Directory created or exists: {base_path}")
    except PermissionError as e:
        print(f"Error: Permission denied creating directory {base_path}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating directory {base_path}: {e}")
        sys.exit(1)
    
    # Create .gitkeep file
    gitkeep_path = base_path / ".gitkeep"
    try:
        # open with 'x' creates the file only if it doesn't exist, 
        # but 'w' is safer if we just want to ensure it exists and is empty.
        # We'll use 'a' or 'w' to ensure it exists.
        with open(gitkeep_path, 'w') as f:
            f.write("") # Empty file
        print(f"Created .gitkeep file: {gitkeep_path}")
    except PermissionError as e:
        print(f"Error: Permission denied creating .gitkeep file {gitkeep_path}: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"Error creating .gitkeep file {gitkeep_path}: {e}")
        sys.exit(1)
    
    print("Task T001a completed successfully.")

if __name__ == "__main__":
    main()
