"""
Script to initialize the project directory structure.
Creates all required folders for the llmXive automated science pipeline.
"""
import os
from pathlib import Path
import sys

def create_directory_tree(root_dir: str = ".") -> None:
    """
    Create the standard project directory tree.
    
    Args:
        root_dir: The root directory where the structure will be created.
                  Defaults to current working directory.
    """
    base_path = Path(root_dir)
    
    # Define the directory structure relative to the root
    directories = [
        "code",
        "data",
        "data/raw",
        "data/processed",
        "artifacts",
        "artifacts/models",
        "artifacts/reports",
        "artifacts/figures",
        "tests"
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created: {full_path}")
            created_count += 1
        else:
            skipped_count += 1
            print(f"Exists:  {full_path}")
    
    print(f"\nDirectory setup complete.")
    print(f"Created: {created_count} directories")
    print(f"Skipped: {skipped_count} (already exist)")

def main():
    """Entry point for the directory setup script."""
    # Determine root directory: if script is run from code/, go up one level
    script_path = Path(__file__).resolve()
    if script_path.name == "setup_directories.py":
        # If running as 'python code/setup_directories.py', root is parent of code/
        root = script_path.parent.parent
    else:
        root = Path(".")
    
    create_directory_tree(str(root))

if __name__ == "__main__":
    main()