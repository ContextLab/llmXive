"""
Script to create the standard project directory structure for llmXive.
This ensures all required folders exist with .gitkeep files for version control.
"""
import os
from pathlib import Path

def create_directory_structure():
    """Create the standard directory structure and .gitkeep files."""
    # Define the base project root (assumed to be the current working directory)
    # In the context of the pipeline, this script is run from the project root.
    base_path = Path.cwd()

    # Define the relative paths to create
    directories = [
        # Phase 1: Setup
        "code",
        "data",
        "tests",
        "docs",
        
        # Phase 1: Data subdirectories
        "data/raw",
        "data/processed",
        
        # Phase 1: Test subdirectories
        "tests/contract",
        "tests/integration",
        "tests/unit",
        
        # Phase 1: Specs subdirectory (as per T001e context)
        "specs/001-multi-property-trade-offs"
    ]

    created_count = 0
    for dir_name in directories:
        full_path = base_path / dir_name
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"  -> Created .gitkeep in {dir_name}")
        else:
            print(f"  -> .gitkeep already exists in {dir_name}")

    print(f"\nDirectory structure setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    create_directory_structure()