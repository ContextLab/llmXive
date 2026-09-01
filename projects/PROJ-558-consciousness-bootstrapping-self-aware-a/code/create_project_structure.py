"""
Project structure creation utility for the Consciousness Bootstrapping project.

This module provides functions to create the required directory structure
for the PROJ-558-consciousness-bootstrapping-self-aware-a project.
"""
import os
from pathlib import Path

def create_structure(root_path: str = None) -> None:
    """
    Create the project directory structure.
    
    Args:
        root_path: The root directory for the project. If None, uses the current
                   working directory.
    
    Creates the following structure:
        projects/PROJ-558-consciousness-bootstrapping-self-aware-a/
        ├── data/
        │   ├── raw/
        │   └── processed/
        ├── code/
        ├── tests/
        └── artifacts/
            ├── checkpoints/
            └── reports/
    """
    if root_path is None:
        root_path = Path.cwd()
    else:
        root_path = Path(root_path)
    
    # Define the project root
    project_name = "PROJ-558-consciousness-bootstrapping-self-aware-a"
    project_root = root_path / "projects" / project_name
    
    # Define all required directories
    directories = [
        project_root,
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests",
        project_root / "artifacts" / "checkpoints",
        project_root / "artifacts" / "reports",
    ]
    
    # Create all directories
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    print(f"\nProject structure created successfully at: {project_root}")

def main():
    """Main entry point for the script."""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="Create the project directory structure for Consciousness Bootstrapping."
    )
    parser.add_argument(
        "--root",
        type=str,
        default=None,
        help="Root directory for the project (default: current working directory)"
    )
    
    args = parser.parse_args()
    create_structure(args.root)

if __name__ == "__main__":
    main()
