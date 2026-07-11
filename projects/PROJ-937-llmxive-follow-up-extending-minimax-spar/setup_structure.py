"""
Script to initialize the project directory structure for llmXive follow-up.
Creates the necessary folders for code, tests, data, and specs as defined in T001.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root based on the task description
    # The task assumes we are creating this structure relative to the current working directory
    # or explicitly creates the path string provided.
    project_root = "projects/PROJ-937-llmxive-follow-up-extending-minimax-spar"
    
    # Define subdirectories to create
    directories = [
        # Code modules
        "code/models",
        "code/heuristics",
        "code/data",
        "code/analysis",
        "code/utils",
        "code/config", # Added for T008 later
        
        # Tests
        "tests/unit",
        "tests/integration",
        
        # Data storage
        "data/raw",
        "data/processed",
        
        # Figures (often needed for analysis)
        "figures",
        
        # Specs (referenced in input)
        "specs",
    ]

    created_count = 0
    skipped_count = 0

    print(f"Creating project structure for: {project_root}")
    
    for dir_path in directories:
        full_path = Path(project_root) / dir_path
        try:
            if full_path.exists():
                print(f"  [SKIP] {full_path} already exists.")
                skipped_count += 1
            else:
                full_path.mkdir(parents=True, exist_ok=True)
                print(f"  [OK] Created: {full_path}")
                created_count += 1
        except Exception as e:
            print(f"  [FAIL] Error creating {full_path}: {e}")
            return 1

    print(f"\nDone. Created {created_count} directories, skipped {skipped_count}.")
    return 0

if __name__ == "__main__":
    sys.exit(main())