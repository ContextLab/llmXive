import os
import sys
from pathlib import Path

def create_structure(root_dir: str = ".") -> None:
    """
    Creates the standard project directory structure for llmXive.
    
    Directories created:
    - src/ (source code)
    - tests/ (test suite)
    - data/ (raw, derived, processed data)
    - specs/ (design documents and specifications)
    
    Args:
        root_dir: The root directory where the structure will be created.
    """
    base_path = Path(root_dir)
    
    # Define the required directories
    directories = [
        "src",
        "src/data",
        "src/models",
        "src/utils",
        "tests",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "data",
        "data/raw",
        "data/derived",
        "data/processed",
        "specs",
        "specs/001-predicting-amine-reactivity",
        "figures",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {full_path}")
            created_count += 1
        else:
            print(f"Directory exists: {full_path}")
    
    # Create .gitkeep files to ensure directories are tracked by git
    # even if they are initially empty
    for dir_path in directories:
        full_path = base_path / dir_path
        gitkeep = full_path / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep: {gitkeep}")
    
    print(f"\nProject structure creation complete. Created {created_count} new directories.")

if __name__ == "__main__":
    create_structure()
