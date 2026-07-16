"""
Script to initialize the project directory structure for PROJ-124.
Creates all required folders for code, data, state, output, tests, and docs.
"""
import os
from pathlib import Path

def create_project_structure():
    """Create the directory structure as specified in T001."""
    # Define all required directories relative to project root
    # Using the path structure defined in tasks.md
    directories = [
        # Code modules
        "code/data",
        "code/models",
        "code/utils",
        "code/config",
        
        # Data storage
        "data/raw",
        "data/processed",
        
        # State management
        "state",
        
        # Output artifacts
        "output",
        
        # Test suites
        "tests/contract",
        "tests/integration",
        "tests/unit",
        
        # Documentation
        "docs/paper",
        "docs/reports"
    ]
    
    # Create each directory
    for dir_path in directories:
        path = Path(dir_path)
        path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {path}")
    
    # Create __init__.py files in Python package directories
    python_packages = [
        "code",
        "code/data",
        "code/models",
        "code/utils",
        "code/config",
        "tests",
        "tests/contract",
        "tests/integration",
        "tests/unit"
    ]
    
    for pkg_path in python_packages:
        init_file = Path(pkg_path) / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created package init: {init_file}")
    
    print("\nProject structure initialization complete.")
    print(f"Total directories created: {len(directories)}")
    
    return directories

if __name__ == "__main__":
    create_project_structure()
