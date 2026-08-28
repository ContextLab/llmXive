"""
Script to create the required data directory structure with .gitkeep files.
This satisfies task T007: Create `data/raw/`, `data/simulated/`, and `data/results/`
directory structure with `.gitkeep` files in each.
"""
import os
import sys
from pathlib import Path


def create_directories(base_path: Path) -> None:
    """
    Create the required data directory structure and .gitkeep files.

    Args:
        base_path: The project root path (parent of 'data' directory)
    """
    # Define the required directories relative to the data folder
    data_dirs = [
        "raw",
        "simulated",
        "results"
    ]

    data_root = base_path / "data"

    # Create the root data directory if it doesn't exist
    data_root.mkdir(parents=True, exist_ok=True)
    print(f"Created data root: {data_root}")

    # Create subdirectories and .gitkeep files
    for dir_name in data_dirs:
        dir_path = data_root / dir_name
        
        # Create directory (parents=True ensures all intermediate dirs are created)
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
        
        # Create .gitkeep file to ensure directory is tracked in git
        gitkeep_path = dir_path / ".gitkeep"
        gitkeep_path.touch()
        print(f"Created .gitkeep: {gitkeep_path}")

    print("\nDirectory structure created successfully:")
    print(f"  {data_root}/")
    for dir_name in data_dirs:
        print(f"    {dir_name}/")
        print(f"      .gitkeep")


def main() -> None:
    """Main entry point for the script."""
    # Determine project root (parent of 'code' directory)
    # This script is located at code/scripts/setup_data_directories.py
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent.parent  # Go up 3 levels to project root

    print(f"Project root: {project_root}")
    print(f"Creating data directory structure...")
    
    create_directories(project_root)
    
    print("\nTask T007 completed: Data directories created with .gitkeep files.")


if __name__ == "__main__":
    main()
