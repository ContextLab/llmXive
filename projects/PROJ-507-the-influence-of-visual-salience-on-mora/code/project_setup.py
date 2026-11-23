"""
Project Setup Module for PROJ-507-the-influence-of-visual-salience-on-mora

This module creates the required directory structure for the research project
as specified in the implementation plan.
"""
import os
from pathlib import Path


def create_project_structure():
    """
    Create the standard project directory structure.

    Creates the following directories relative to the project root:
    - code/
    - data/raw/
    - data/processed/
    - data/survey/
    - data/synth/ (for synthetic data separation)
    - tests/
    - tests/unit/
    - tests/integration/
    - config/
    - docs/
    - figures/

    Returns:
        Path: The project root directory where structure was created.
    """
    # Define the base directory (current working directory is assumed to be project root)
    base_dir = Path.cwd()

    # Define required directories
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/survey",
        "data/synth",
        "tests/unit",
        "tests/integration",
        "config",
        "docs",
        "figures",
    ]

    created_count = 0
    for dir_path in directories:
        full_path = base_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

    # Create .gitkeep files in empty directories to ensure they are tracked by git
    for dir_path in directories:
        full_path = base_dir / dir_path
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in: {full_path}")

    print(f"\nProject structure created/verified at: {base_dir}")
    print(f"New directories created: {created_count}")
    return base_dir


def main():
    """Entry point for running the script directly."""
    print("Initializing project structure for PROJ-507...")
    create_project_structure()
    print("Done.")


if __name__ == "__main__":
    main()
