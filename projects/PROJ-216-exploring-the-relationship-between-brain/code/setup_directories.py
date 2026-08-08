"""
Script to initialize the project directory structure and create __init__.py files.
This satisfies Task T001.
"""
import os
import sys
from pathlib import Path
from typing import List

def create_directories(root_dir: Path) -> None:
    """
    Creates the required directory structure for the project.
    
    Args:
        root_dir: The root path of the project.
    """
    directories = [
        "data/raw",
        "data/interim",
        "data/processed",
        "code",
        "tests/unit",
        "tests/integration",
        "reports"
    ]
    
    for dir_path in directories:
        full_path = root_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def create_init_files(root_dir: Path) -> None:
    """
    Creates __init__.py files in all directory paths to make them Python packages.
    
    Args:
        root_dir: The root path of the project.
    """
    init_paths = [
        "code",
        "tests",
        "tests/unit",
        "tests/integration"
    ]
    
    for rel_path in init_paths:
        file_path = root_dir / rel_path / "__init__.py"
        # Ensure parent exists
        file_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write a docstring-only __init__.py
        content = f'"""\n{rel_path} Module\n"""\n'
        
        # Only write if file doesn't exist or is empty (optional, but good practice)
        if not file_path.exists() or file_path.stat().st_size == 0:
            with open(file_path, 'w') as f:
                f.write(content)
            print(f"Created __init__.py: {file_path}")
        else:
            print(f"Skipped existing __init__.py: {file_path}")

def main() -> int:
    """
    Main entry point for the directory setup script.
    
    Returns:
        Exit code (0 for success, 1 for failure).
    """
    # Determine project root (parent of 'code' directory)
    current_file = Path(__file__).resolve()
    # Assuming this script is in code/setup_directories.py
    # Project root is two levels up
    project_root = current_file.parent.parent
    
    print(f"Initializing project structure at: {project_root}")
    
    try:
        create_directories(project_root)
        create_init_files(project_root)
        print("Project structure initialization complete.")
        return 0
    except Exception as e:
        print(f"Error during initialization: {e}", file=sys.stderr)
        return 1

if __name__ == "__main__":
    sys.exit(main())
