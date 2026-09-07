"""
Script to create the project directory structure as per the implementation plan.
This addresses Task T001: Create project structure per implementation plan.
"""
import os
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Create a directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    else:
        print(f"Directory already exists: {path}")

def main():
    """Create all required project directories."""
    # Determine project root (assuming script is in code/scripts/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    # Define required directories relative to project root
    required_dirs = [
        'src',
        'tests',
        'contracts',
        'data',
        'data/raw',
        'data/processed',
        'data/logs',
        'reports',
        'docs',
        'state',
        'state/projects'
    ]

    print(f"Creating project structure in: {project_root}")
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        ensure_dir(dir_path)

    print("Project structure creation complete.")

if __name__ == "__main__":
    main()