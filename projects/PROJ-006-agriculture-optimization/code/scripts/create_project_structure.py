"""
Script to create the project directory structure as per T001.
"""
import os
from pathlib import Path

def ensure_dir(path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    path.mkdir(parents=True, exist_ok=True)

def main():
    """Create all required project directories."""
    # Determine project root (assuming script is in code/scripts/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent

    required_dirs = [
        'src',
        'tests',
        'contracts',
        'data',
        'data/raw',
        'data/processed',
        'data/logs',
        'reports',
        'state',
        'state/projects',
        'docs'
    ]

    print(f"Creating project structure in: {project_root}")
    for dir_name in required_dirs:
        dir_path = project_root / dir_name
        ensure_dir(dir_path)
        print(f"  Created: {dir_path}")

    print("Project structure creation complete.")

if __name__ == "__main__":
    main()