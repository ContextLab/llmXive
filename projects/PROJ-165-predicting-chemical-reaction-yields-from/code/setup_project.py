"""
Project Structure Setup Script for llmXive Pipeline.
Creates the standard directory hierarchy required for the research project.
"""
import os
import sys
from pathlib import Path

def create_structure(base_dir: str = ".") -> None:
    """
    Creates the standard project directory structure under the specified base directory.
    
    Structure created:
    - code/ (source code)
      - src/
        - cli/
        - data/
        - models/
        - eval/
        - utils/
        - config/
      - tests/
        - unit/
        - integration/
        - contract/
    - data/
      - raw/
      - processed/
      - artifacts/
      - figures/
    - state/ (for state tracking and hashes)
    - docs/
    - logs/
    
    Args:
        base_dir: Root directory where the structure will be created. Defaults to current directory.
    """
    base_path = Path(base_dir)
    
    # Define the directory structure to create
    directories = [
        # Source code structure
        "code/src/cli",
        "code/src/data",
        "code/src/models",
        "code/src/eval",
        "code/src/utils",
        "code/src/config",
        "code/tests/unit",
        "code/tests/integration",
        "code/tests/contract",
        
        # Data structure
        "data/raw",
        "data/processed",
        "data/artifacts",
        "data/figures",
        
        # State and documentation
        "state",
        "docs",
        "logs",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = base_path / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            # Check if it's actually a directory
            if not full_path.is_dir():
                raise RuntimeError(f"Path exists but is not a directory: {full_path}")
    
    # Create __init__.py files to make directories Python packages
    init_files = [
        "code/src/__init__.py",
        "code/src/cli/__init__.py",
        "code/src/data/__init__.py",
        "code/src/models/__init__.py",
        "code/src/eval/__init__.py",
        "code/src/utils/__init__.py",
        "code/src/config/__init__.py",
        "code/tests/__init__.py",
        "code/tests/unit/__init__.py",
        "code/tests/integration/__init__.py",
        "code/tests/contract/__init__.py",
    ]
    
    for init_file in init_files:
        full_path = base_path / init_file
        if not full_path.exists():
            full_path.touch()
            print(f"Created package init: {full_path}")
    
    print(f"\nProject structure setup complete. {created_count} new directories created.")
    print(f"Base directory: {base_path.resolve()}")

if __name__ == "__main__":
    # If run directly, create structure in current directory
    create_structure()
