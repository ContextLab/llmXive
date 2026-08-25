import os
import sys
from pathlib import Path

def create_directory_structure():
    """Create the project directory structure as defined in T004."""
    base_dir = Path.cwd()
    
    directories = [
        "code/experiment",
        "code/experiment/tests",
        "code/analysis",
        "code/analysis/tests",
        "data/raw",
        "data/processed",
        "docs",
        "specs/001-perceived-agency-trust/contracts",
    ]
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

def create_init_files():
    """Create __init__.py files in all code/ subdirectories and tests/ subdirectories."""
    base_dir = Path.cwd()
    
    init_paths = [
        "code",
        "code/experiment",
        "code/experiment/tests",
        "code/analysis",
        "code/analysis/tests",
        "code/research",
    ]
    
    for dir_path in init_paths:
        full_path = base_dir / dir_path
        init_file = full_path / "__init__.py"
        
        # Create directory if it doesn't exist
        full_path.mkdir(parents=True, exist_ok=True)
        
        # Create __init__.py if it doesn't exist
        if not init_file.exists():
            init_file.touch()
            print(f"Created __init__.py: {init_file}")
        else:
            print(f"__init__.py already exists: {init_file}")

def main():
    """Main entry point for creating project structure."""
    print("Creating project directory structure...")
    create_directory_structure()
    
    print("\nCreating __init__.py files...")
    create_init_files()
    
    print("\nProject structure setup complete.")

if __name__ == "__main__":
    main()