"""
Script to initialize the llmXive project directory structure.
Creates directories as specified in plan.md:
- code/
- data/raw
- data/processed
- results
- tests/unit
- tests/integration
"""
import os
import sys
from pathlib import Path

def create_project_structure(root_dir: str = ".") -> None:
    """
    Create the required project directory structure.
    
    Args:
        root_dir: Root directory for the project (default: current directory)
    """
    base_path = Path(root_dir)
    
    # Define required directories
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "results",
        "tests/unit",
        "tests/integration"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {full_path}")
    
    # Create __init__.py files to make directories Python packages
    init_files = [
        base_path / "code" / "__init__.py",
        base_path / "data" / "__init__.py",
        base_path / "data" / "raw" / "__init__.py",
        base_path / "data" / "processed" / "__init__.py",
        base_path / "results" / "__init__.py",
        base_path / "tests" / "__init__.py",
        base_path / "tests" / "unit" / "__init__.py",
        base_path / "tests" / "integration" / "__init__.py"
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created: {init_file}")
        else:
            print(f"File already exists: {init_file}")
    
    print(f"\nProject structure initialization complete.")
    print(f"Created {created_count} new directories.")

def main():
    """Entry point for the script."""
    create_project_structure()
    print("\nDirectory structure created successfully.")

if __name__ == "__main__":
    main()
