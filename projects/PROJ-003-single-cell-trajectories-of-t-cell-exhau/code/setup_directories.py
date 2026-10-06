"""
Directory setup module for the Single-Cell Trajectories of T-Cell Exhaustion project.

This module creates the required directory structure for data and tests as specified
in the project plan.
"""
import os
from pathlib import Path

def setup_directories():
    """
    Create the required directory structure for the project.
    
    Creates the following directories relative to the project root:
    - data/raw/
    - data/processed/
    - data/results/
    - tests/unit/
    - tests/integration/
    
    Returns:
        Path: The project root path where directories were created.
    """
    # Determine project root (assuming this script is in code/ directory)
    # We look for the parent of the code directory, or use current working directory
    # if running from project root
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent if code_dir.name == "code" else code_dir.parent.parent.parent
    
    # Define required directories
    directories = [
        "data/raw",
        "data/processed",
        "data/results",
        "tests/unit",
        "tests/integration"
    ]
    
    # Create directories
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Create __init__.py files for tests directories to make them proper packages
    for pkg_dir in ["tests/unit", "tests/integration"]:
        init_file = project_root / pkg_dir / "__init__.py"
        init_file.touch(exist_ok=True)
        print(f"Created package init: {init_file}")
    
    return project_root

if __name__ == "__main__":
    project_root = setup_directories()
    print(f"Directory setup complete. Project root: {project_root}")
