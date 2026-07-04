"""
Script to create the 'docs/' directory for the project.
This is part of the initial setup phase (Phase 1).
"""
import os
import sys
from pathlib import Path

def create_directory(dir_path: Path) -> bool:
    """
    Creates a directory if it does not exist.
    
    Args:
        dir_path: Path object representing the directory to create.
        
    Returns:
        True if the directory was created or already exists, False otherwise.
    """
    try:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Directory '{dir_path}' created successfully or already exists.")
        return True
    except Exception as e:
        print(f"Error creating directory '{dir_path}': {e}")
        return False

def main():
    """Main entry point for creating the docs directory."""
    # Define the docs directory relative to the project root
    # Assuming this script is run from the project root or code/ subdirectory
    project_root = Path(__file__).resolve().parent.parent
    docs_dir = project_root / "docs"
    
    print(f"Ensuring directory exists: {docs_dir}")
    success = create_directory(docs_dir)
    
    if success:
        # Create a placeholder README.md inside docs to ensure the directory is non-empty
        # and satisfies the "evidence" requirement for directory creation.
        readme_path = docs_dir / "README.md"
        if not readme_path.exists():
            readme_content = """# Project Documentation

This directory contains documentation for the llmXive automated science pipeline project.

## Contents

- `README.md`: This file.
"""
            readme_path.write_text(readme_content)
            print(f"Placeholder file created: {readme_path}")
        return 0
    else:
        return 1

if __name__ == "__main__":
    sys.exit(main())