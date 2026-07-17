"""
Script to explicitly create the required directory structure for the llmXive project.
This ensures all necessary folders exist for data, code, tests, and documentation.
"""
import os
import sys
from pathlib import Path

def main():
    # Determine the project root based on the task description
    # The task specifies paths relative to: projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/
    # We will assume the script is run from the repository root or the project root.
    # To be safe, we construct the path relative to the script's location if it's in 'code/',
    # or we look for the specific project directory.
    
    script_dir = Path(__file__).resolve().parent
    # If the script is in code/, we look up one level to the project root
    # However, the task says "in projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2/"
    # Let's assume the current working directory is the project root or we are inside the project folder.
    
    # We will create the structure relative to the current working directory (CWD)
    # as is standard for such setup scripts, but we will verify the target path exists.
    
    # Target project path relative to CWD or absolute if we detect it
    # The prompt implies we are working inside the project directory.
    # Let's define the root as the directory containing 'code', 'data', etc.
    # If we are in 'projects/PROJ-979-llmxive-follow-up-extending-loopcoder-v2', that is the root.
    
    project_root = Path.cwd()
    
    # Define the required directories relative to the project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "code/src",
        "code/tests",
        "code/notebooks",
        "paper",
        "state",
        "contracts"
    ]
    
    created_count = 0
    existing_count = 0
    
    print(f"Creating directory structure in: {project_root}")
    
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        
        if full_path.exists():
            if full_path.is_dir():
                print(f"[SKIP] Directory already exists: {full_path}")
                existing_count += 1
            else:
                print(f"[ERROR] Path exists but is not a directory: {full_path}")
                sys.exit(1)
        else:
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"[CREATED] {full_path}")
            created_count += 1
    
    print(f"\nSummary: {created_count} directories created, {existing_count} already existed.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
