"""
T001: Create project structure per implementation plan.

This script initializes the directory structure required for the llmXive
automated science pipeline. It creates the following directories relative
to the project root:

- code/
- data/raw/
- data/processed/
- tests/

It also creates a .gitkeep file in each directory to ensure they are
tracked by version control even when empty.
"""
import os
from pathlib import Path

def create_project_structure():
    """Create the required project directories."""
    # Define the base directories relative to the current working directory
    base_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
    ]

    created_dirs = []
    for dir_path in base_dirs:
        full_path = Path(dir_path)
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(full_path))
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")

        # Create .gitkeep to ensure directory is tracked by git
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"  -> Created .gitkeep in {full_path}")

    return created_dirs

if __name__ == "__main__":
    print("Initializing project structure for PROJ-163...")
    created = create_project_structure()
    if created:
        print(f"\nSuccessfully created {len(created)} directories.")
    else:
        print("\nNo new directories were created; structure already exists.")
    print("Project structure initialization complete.")
