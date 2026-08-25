"""
Script to create the project directory structure as defined in the implementation plan.
This script ensures all required directories exist for the project to function correctly.
"""
import os
from pathlib import Path


def ensure_dir(path: Path) -> None:
    """Create a directory if it does not exist."""
    if not path.exists():
        path.mkdir(parents=True, exist_ok=True)
    if not path.is_dir():
        raise ValueError(f"Path exists but is not a directory: {path}")


def main() -> None:
    """Create the full project structure."""
    # Determine project root based on script location
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
        'state',
        'state/projects',
        'docs',
        'figures',
        'specs',
        'specs/001-climate-smart-eval'
    ]

    print(f"Project root detected at: {project_root}")

    for dir_path_str in required_dirs:
        full_path = project_root / dir_path_str
        ensure_dir(full_path)
        print(f"Ensured directory: {full_path}")

    print("Project structure creation complete.")


if __name__ == "__main__":
    main()