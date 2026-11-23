"""
Setup script for creating project directory structure.
"""
import os
import sys
from pathlib import Path

def create_directories():
    """Create the standard project directory structure."""
    project_root = Path(__file__).resolve().parent.parent

    directories = [
        "data/raw",
        "data/processed",
        "data/figures",
        "outputs",
        "logs",
        "config",
        "code/data_models"
    ]

    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")

    # Create .gitkeep files
    for dir_path in directories:
        full_path = project_root / dir_path
        gitkeep = full_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep in: {full_path}")

def main():
    """Main entry point."""
    create_directories()
    print("Directory structure setup complete.")

if __name__ == "__main__":
    main()
