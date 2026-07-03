"""
Main entry point to execute the project initialization task T001.
This script creates the root directory and all required subdirectories
idempotently.
"""
import sys
from pathlib import Path

# Add the current directory to sys.path to allow imports of sibling modules
current_dir = Path(__file__).resolve().parent
sys.path.insert(0, str(current_dir))

from setup_project import ensure_directory, create_gitkeep

def main() -> None:
    """Execute T001: Initialize project structure."""
    # Determine the project root relative to the code directory
    # Assuming the script is run from the repository root or code directory
    # We aim to create the structure under 'projects/PROJ-355-...'
    
    # Determine the repository root by looking for a parent 'projects' folder 
    # or assuming the script is run from the repo root.
    # For robustness, we assume the script is run from the repo root.
    repo_root = Path(__file__).resolve().parent.parent
    
    project_name = "PROJ-355-predicting-the-impact-of-impurity-cluste"
    target_root = repo_root / "projects" / project_name
    
    subdirs = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "tests/unit",
        "tests/integration"
    ]

    print(f"Initializing project structure at: {target_root}")
    
    # Create the root project directory
    ensure_directory(target_root)

    # Create subdirectories and .gitkeep files
    for subdir in subdirs:
        dir_path = target_root / subdir
        ensure_directory(dir_path)
        create_gitkeep(dir_path)

    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()