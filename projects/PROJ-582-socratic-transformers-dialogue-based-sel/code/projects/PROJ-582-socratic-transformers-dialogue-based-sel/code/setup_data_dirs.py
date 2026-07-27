"""
Setup script for T004: Create data directory structure and .gitkeep files.

This script creates the required data directories:
- data/raw/
- data/processed/
- data/results/

And adds .gitkeep files to ensure they are tracked by git even when empty.
"""
import os
import sys
from pathlib import Path


def create_gitkeep(directory: Path) -> None:
    """Create a .gitkeep file in the specified directory."""
    gitkeep_path = directory / ".gitkeep"
    # Write a minimal comment to explain the file's purpose
    gitkeep_path.write_text(
        "# This file ensures the directory is tracked by git even when empty.\n"
    )
    print(f"Created: {gitkeep_path}")


def main() -> int:
    """Main entry point for the data directory setup script."""
    # Determine the project root (parent of the code directory)
    # The script is located at: code/projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/setup_data_dirs.py
    # We want to create data dirs relative to the project root
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent  # Go up two levels to project root
    
    # Define the data directories
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/results",
    ]
    
    print(f"Setting up data directories in: {project_root}")
    
    for dir_path in data_dirs:
        full_path = project_root / dir_path
        
        # Create the directory if it doesn't exist
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
        
        # Create .gitkeep file
        create_gitkeep(full_path)
    
    print("\nData directory setup complete!")
    return 0


if __name__ == "__main__":
    sys.exit(main())
