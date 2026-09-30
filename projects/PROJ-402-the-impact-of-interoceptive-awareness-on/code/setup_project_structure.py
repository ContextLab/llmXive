"""
Project Structure Setup Script for llmXive Automated Science Pipeline.

This script initializes the required directory structure and placeholder files
for the research project as defined in the implementation plan.

Creates:
- code/ (source code directory)
- tests/ (test suite directory)
- data/ (raw and derived data directory)
- results/ (analysis outputs and reports directory)
- contracts/ (data schema definitions)
- state/ (pipeline state tracking)
- specs/ (feature specifications)
- figures/ (visualizations)
"""

import os
from pathlib import Path
from typing import List

def create_directories(base_path: Path, directories: List[str]) -> None:
    """
    Create a list of directories relative to the base path.
    
    Args:
        base_path: The root directory for the project.
        directories: List of relative directory paths to create.
    """
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def create_init_files(base_path: Path, directories: List[str]) -> None:
    """
    Create __init__.py files in Python package directories to make them importable.
    
    Args:
        base_path: The root directory for the project.
        directories: List of relative directory paths that should be Python packages.
    """
    python_packages = ['code', 'tests', 'code/utils', 'code/tests']
    for pkg in python_packages:
        full_path = base_path / pkg / '__init__.py'
        # Ensure the directory exists first
        full_path.parent.mkdir(parents=True, exist_ok=True)
        full_path.touch(exist_ok=True)
        print(f"Created __init__.py: {full_path}")

def create_gitkeep_files(base_path: Path, directories: List[str]) -> None:
    """
    Create .gitkeep files in data directories to ensure they are tracked by git
    even when empty.
    
    Args:
        base_path: The root directory for the project.
        directories: List of relative directory paths that should contain .gitkeep.
    """
    data_dirs = ['data/raw', 'data/derived', 'results', 'figures', 'contracts', 'state/projects']
    for dir_path in data_dirs:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        gitkeep_path = full_path / '.gitkeep'
        gitkeep_path.touch(exist_ok=True)
        print(f"Created .gitkeep: {gitkeep_path}")

def main() -> None:
    """
    Main entry point for project structure setup.
    Creates all required directories and initialization files.
    """
    # Define the base path (current working directory is assumed to be project root)
    base_path = Path.cwd()
    
    # Define the required directory structure
    # Phase 1: Setup directories
    required_dirs = [
        'code',
        'code/utils',
        'code/tests',
        'tests',
        'data',
        'data/raw',
        'data/derived',
        'results',
        'contracts',
        'state',
        'state/projects',
        'specs',
        'figures',
        'docs'
    ]
    
    print(f"Initializing project structure in: {base_path}")
    print("-" * 50)
    
    # Create directories
    create_directories(base_path, required_dirs)
    
    # Create Python package init files
    create_init_files(base_path, required_dirs)
    
    # Create .gitkeep files for data tracking
    create_gitkeep_files(base_path, required_dirs)
    
    print("-" * 50)
    print("Project structure initialization complete.")
    print("Next steps: Install dependencies (T002a) and configure linting (T003).")

if __name__ == "__main__":
    main()
