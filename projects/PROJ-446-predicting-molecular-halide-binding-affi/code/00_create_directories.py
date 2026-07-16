import os
from pathlib import Path

def main():
    """
    Create the standard directory structure for the project.
    Assumes the project root 'projects/PROJ-446-predicting-molecular-halide-binding-affi' exists.
    """
    project_root = Path("projects/PROJ-446-predicting-molecular-halide-binding-affi")
    
    if not project_root.exists():
        print(f"Error: Project root {project_root} does not exist. Run 00_create_project_root.py first.")
        return False

    # Define directories to create
    directories = [
        "code",
        "code/utils",
        "data",
        "docs",
        "data/raw",
        "data/processed",
        "data/simulated",
        "docs/paper"
    ]

    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {full_path}")

    return True

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)
