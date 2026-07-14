"""
Scaffolding script to create the project directory structure.
This script generates the required directories for the material strength prediction project.
"""
import os
from pathlib import Path
import sys

def main():
    # Define the project root based on the task description
    # The task asks to create the tree under projects/PROJ-477-predicting-material-strength-from-micros/
    # However, looking at the existing API surface, the code lives in 'code/', tests in 'tests/', data in 'data/', results in 'results/'
    # relative to the project root.
    # The task description mentions: "projects/PROJ-477-predicting-material-strength-from-micros/"
    # But the existing files (e.g., code/utils/config.py) imply the project root IS the directory containing 'code', 'data', etc.
    # We will create the structure relative to the current working directory, assuming this script runs from the repo root.
    # If the project is meant to be inside a 'projects' folder, we handle that, but standard practice for these prompts
    # is to create the root structure where the script is run.
    
    # Let's align with the "Path Conventions" in tasks.md: "Single project: src/, tests/ at repository root"
    # But the existing API surface shows 'code/', 'data/', 'tests/', 'results/'.
    # We will create the directories: code, data/raw, data/processed, tests, results.
    
    project_root = Path.cwd()
    
    # Define the directory structure to create
    directories = [
        "code",
        "code/data",
        "code/models",
        "code/train",
        "code/eval",
        "code/utils",
        "data",
        "data/raw",
        "data/processed",
        "data/external", # Often needed for downloaded data
        "tests",
        "tests/unit",
        "tests/integration",
        "results",
        "figures",
        "scripts" # For the scaffold script itself if moved, or other tools
    ]
    
    created_count = 0
    skipped_count = 0
    
    print(f"Creating project structure in: {project_root}")
    
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists:  {full_path}")
            skipped_count += 1
    
    print(f"\nScaffolding complete.")
    print(f"Created: {created_count} directories")
    print(f"Skipped: {skipped_count} (already exist)")
    
    # Verify specific required paths
    required_paths = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "results"
    ]
    
    all_present = True
    for r_path in required_paths:
        if not (project_root / r_path).exists():
            print(f"ERROR: Required path missing: {r_path}")
            all_present = False
    
    if all_present:
        print("SUCCESS: All required directories are present.")
        sys.exit(0)
    else:
        print("FAILURE: Some required directories are missing.")
        sys.exit(1)

if __name__ == "__main__":
    main()