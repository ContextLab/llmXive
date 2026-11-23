"""
Task T001: Create project directory structure.

This script creates the required directory structure for the llmXive project:
- code/
- data/ (with raw, processed, logs subdirectories)
- contracts/
- tests/ (with unit, integration subdirectories)
- docs/
- figures/

It ensures all directories exist and creates a .gitkeep file in each to ensure
they are tracked by version control.
"""
import os
from pathlib import Path


def ensure_directories() -> None:
    """Create the project directory structure as per the implementation plan."""
    base_path = Path(".")
    
    # Define the directory structure
    directories = [
        "code",
        "code/analysis",
        "code/preprocess",
        "code/reports",
        "code/utils",
        "data",
        "data/raw",
        "data/processed",
        "data/logs",
        "data/figures",
        "contracts",
        "tests",
        "tests/unit",
        "tests/integration",
        "docs",
        "figures",
    ]
    
    # Create each directory
    for dir_path in directories:
        full_path = base_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        
        # Create .gitkeep to ensure directory is tracked by git
        gitkeep_path = full_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
        print(f"Created/verified directory: {full_path}")
    
    print("\nDirectory structure creation complete.")


def main() -> None:
    """Entry point for the script."""
    ensure_directories()


if __name__ == "__main__":
    main()
