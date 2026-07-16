"""
Project structure setup script for PROJ-503.
Creates the required directory hierarchy as specified in T001.
"""
import os
import sys
from pathlib import Path

def main():
    # Define the project root based on the task requirements
    # The task specifies paths relative to the repo root, e.g., projects/PROJ-...
    # We assume the script is run from the repo root or we construct the absolute path.
    # To be safe and robust, we'll determine the project root relative to this file's location
    # or use the current working directory if this file is in the code/ directory.
    
    # The task requires paths like:
    # projects/PROJ-503-predicting-plant-defense-compound-produc/code/
    # ...
    
    # Since the API surface shows this file is at code/setup_project.py,
    # we assume the script is executed from the project root (which contains 'projects' dir)
    # or we are inside the project directory.
    
    # Let's construct the base path. The task description implies the project is
    # at `projects/PROJ-503-predicting-plant-defense-compound-produc/`.
    # If we are running `python code/setup_project.py` from the repo root:
    
    repo_root = Path.cwd()
    
    # Check if we are already inside the project directory or if we need to navigate
    # The task path is explicit: projects/PROJ-503-predicting-plant-defense-compound-produc
    # Let's assume the standard structure where this script is run from the repo root
    # and the project is a subdirectory.
    
    project_dir_name = "PROJ-503-predicting-plant-defense-compound-produc"
    
    # Attempt to find the project directory
    # Strategy 1: Check if current dir ends with the project name
    if repo_root.name == project_dir_name:
        project_root = repo_root
    # Strategy 2: Check if parent dir contains the project name (e.g. running from repo root)
    elif (repo_root / project_dir_name).exists():
        project_root = repo_root / project_dir_name
    # Strategy 3: Check if we are in a 'projects' subfolder
    elif (repo_root / "projects" / project_dir_name).exists():
        project_root = repo_root / "projects" / project_dir_name
    else:
        # Fallback: assume current directory is the project root if it matches the pattern
        # or just create relative to current
        print(f"Warning: Could not locate project directory '{project_dir_name}' in expected locations.")
        print(f"Creating directories relative to current working directory: {repo_root}")
        project_root = repo_root / project_dir_name
        project_root.mkdir(parents=True, exist_ok=True)

    # Define the required directories
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/paired",
        "logs",
        "outputs/models",
        "docs",
        "tests/contract",
        "tests/integration",
        "tests/unit"
    ]

    created_count = 0
    skipped_count = 0

    print(f"Setting up project structure at: {project_root}")

    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            print(f"Exists: {full_path}")
            skipped_count += 1

    # Verify the structure by listing created directories
    print(f"\nProject structure setup complete.")
    print(f"Created: {created_count} directories")
    print(f"Skipped (already exist): {skipped_count} directories")
    
    # Print the final tree structure (depth 1)
    print("\nDirectory structure:")
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        print(f"  {full_path.relative_to(project_root) if full_path.is_relative_to(project_root) else full_path}")

    return 0

if __name__ == "__main__":
    sys.exit(main())