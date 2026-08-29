"""
Project structure setup script for llmXive automated science pipeline.
Creates the required directory tree for the perovskite thermal conductivity project.
"""
import os
import sys
from pathlib import Path

def setup_project_structure():
    """
    Creates the exact directory tree required by the project specifications:
    - src/
    - tests/
    - data/raw/
    - data/cleaned/
    - data/results/
    - figures/
    - contracts/
    
    Also creates __init__.py files in all Python package directories.
    """
    # Define the base directories relative to the project root
    # The script assumes it is run from the project root or code/ directory
    # We will create them relative to the current working directory
    
    project_root = Path.cwd()
    
    # Define all required directories
    required_dirs = [
        "src",
        "tests",
        "data/raw",
        "data/cleaned",
        "data/results",
        "figures",
        "contracts"
    ]
    
    # Directories that need __init__.py to be valid Python packages
    package_dirs = [
        "src",
        "tests",
        "src/ingest",
        "src/cleaning",
        "src/descriptors",
        "src/analysis",
        "src/utils",
        "src/config",
        "tests/unit",
        "tests/integration",
        "tests/contract"
    ]
    
    print(f"Setting up project structure in: {project_root}")
    
    created_count = 0
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create __init__.py files for Python packages
    for pkg_path in package_dirs:
        full_path = project_root / pkg_path / "__init__.py"
        if not full_path.exists():
            full_path.parent.mkdir(parents=True, exist_ok=True)
            full_path.touch()
            print(f"Created package init: {full_path}")
            created_count += 1
        else:
            print(f"Package init already exists: {full_path}")
    
    print(f"\nProject structure setup complete. Created {created_count} new items.")
    return True

if __name__ == "__main__":
    success = setup_project_structure()
    sys.exit(0 if success else 1)
