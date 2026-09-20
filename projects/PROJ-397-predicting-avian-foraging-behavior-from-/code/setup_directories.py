"""
Script to initialize the project directory structure for PROJ-397.
Creates required directories and .gitkeep files as per T001.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root relative to the script location or current working directory
    # The task specifies paths relative to the project root, but artifacts must be under code/
    # We will create the structure relative to the current working directory (assumed to be project root)
    # However, the task description says: "Create directories projects/PROJ-397-.../code/..."
    # And the constraint says: "All artifact paths are relative to the project root and MUST live under code/, data/..."
    # This implies the project root is where we run the script.
    # The task description path "projects/PROJ-397-..." seems to be a nested path from a larger repo,
    # but the constraint says "Stay inside the project tree... under code/".
    # Given the existing API surface shows files like `code/utils/config.py`, the project root is likely the directory containing `code/`.
    # The task description might be slightly misaligned with the actual project root convention used in this repo.
    # I will interpret T001 as creating the directories INSIDE `code/` as requested by the constraint and existing structure.
    # The task says: "Create directories projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/, models/..."
    # If I am running from the project root, and the project is PROJ-397, then the root IS the project root.
    # The existing files are in `code/`. So `code/data/`, `code/models/`, etc. are the targets.
    
    # Let's re-read carefully: "Create directories projects/PROJ-397-predicting-avian-foraging-behavior-from-/code/data/, models/, viz/, notebooks/, utils/, and tests/"
    # This looks like the path from a super-repo root.
    # But the constraint says: "All artifact paths are relative to the project root and MUST live under code/, data/, tests/, or the project's specs/ feature directory."
    # And the existing API surface shows `code/utils/config.py`.
    # So the "project root" for this agent is the directory containing `code/`.
    # Therefore, the directories to create are:
    # code/data/
    # code/models/
    # code/viz/
    # code/notebooks/
    # code/utils/
    # code/tests/
    
    # Wait, the task says "Create directories ... code/data/, models/, viz/..."
    # It lists `code/data/` but then `models/`, `viz/` without the `code/` prefix in the list?
    # "Create directories projects/.../code/data/, models/, viz/, notebooks/, utils/, and tests/"
    # This implies the list is relative to `code/`.
    # So the targets are:
    # code/data
    # code/models
    # code/viz
    # code/notebooks
    # code/utils
    # code/tests
    
    # Let's verify with existing files. `code/utils/config.py` exists. `code/data/aggregate.py` exists.
    # So these directories MUST exist or be created.
    # The task is to ensure they exist and have .gitkeep.
    
    base_path = Path(".")
    code_path = base_path / "code"
    
    # Ensure the code directory exists first
    code_path.mkdir(parents=True, exist_ok=True)
    
    directories = [
        "data",
        "models",
        "viz",
        "notebooks",
        "utils",
        "tests"
    ]
    
    created_count = 0
    for dir_name in directories:
        dir_path = code_path / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        
        gitkeep_path = dir_path / ".gitkeep"
        # touch .gitkeep (create if not exists, or update timestamp)
        gitkeep_path.touch()
        created_count += 1
        print(f"Created/Verified: {dir_path} and {gitkeep_path}")
    
    print(f"Successfully initialized {created_count} directories with .gitkeep files.")
    return 0

if __name__ == "__main__":
    sys.exit(main())