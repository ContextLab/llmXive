"""
Script to initialize the project directory structure and package files.
This script creates the required directories and empty __init__.py files
to satisfy T001a and T001b.
"""
import os
from pathlib import Path

def main():
    # Define the project root relative to where this script runs
    # Assuming this script is placed at the project root or the path is relative to current dir
    project_root = Path(__file__).parent / "projects" / "PROJ-819-llmxive-follow-up-extending-heterogeneou"
    
    # Define the directory structure to create
    dirs_to_create = [
        "code",
        "code/cache",
        "code/pipeline",
        "code/analysis",
        "code/data",
        "code/reproducibility",
        "data",
        "data/raw",
        "data/derived",
        "tests",
        "tests/unit",
        "tests/integration",
        "state"
    ]
    
    # Create directories
    for dir_path in dirs_to_create:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Define __init__.py locations
    init_paths = [
        "code/__init__.py",
        "code/cache/__init__.py",
        "code/pipeline/__init__.py",
        "code/analysis/__init__.py",
        "code/data/__init__.py",
        "code/reproducibility/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py"
    ]
    
    # Create empty __init__.py files
    for init_path in init_paths:
        full_path = project_root / init_path
        full_path.touch()
        print(f"Created empty file: {full_path}")
    
    # Create .gitkeep files for data directories to ensure they are tracked in git
    gitkeep_paths = [
        "data/raw/.gitkeep",
        "data/derived/.gitkeep",
        "state/.gitkeep"
    ]
    for gp in gitkeep_paths:
        full_path = project_root / gp
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.write_text("# Placeholder to ensure directory exists\n")
        print(f"Created .gitkeep: {full_path}")

if __name__ == "__main__":
    main()