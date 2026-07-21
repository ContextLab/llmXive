"""
Project Structure Initialization Script.

Creates the foundational directory structure for the llmXive plant defense allocation project.
This script ensures all required directories exist before any data processing begins.

Structure created:
- code/ (source code)
  - src/ (main source)
    - utils/
    - data/
    - analysis/
    - cli/
  - tests/
    - unit/
    - integration/
    - contract/
- data/
  - raw/ (unmodified downloaded data)
  - processed/ (normalized matrices, QC results)
  - traits/ (compiled trait data)
  - manifests/ (data manifests)
  - synthetic/ (synthetic test data)
- specs/ (feature specifications)
- docs/ (documentation)
- figures/ (plots and visualizations)
"""
import os
import sys
from pathlib import Path

def create_directory_structure(root_path: Path) -> None:
    """
    Create the complete project directory structure.
    
    Args:
        root_path: The root directory where the project structure will be created.
    """
    directories = [
        # Source code structure
        "code/src/utils",
        "code/src/data",
        "code/src/analysis",
        "code/src/cli",
        
        # Test structure
        "code/tests/unit",
        "code/tests/integration",
        "code/tests/contract",
        
        # Data structure
        "data/raw",
        "data/processed",
        "data/traits",
        "data/manifests",
        "data/synthetic",
        
        # Documentation and specs
        "specs",
        "docs",
        "figures",
    ]
    
    for dir_path in directories:
        full_path = root_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created: {full_path}")
    
    # Create placeholder __init__.py files for Python packages
    init_files = [
        "code/src/__init__.py",
        "code/src/utils/__init__.py",
        "code/src/data/__init__.py",
        "code/src/analysis/__init__.py",
        "code/src/cli/__init__.py",
        "code/tests/__init__.py",
        "code/tests/unit/__init__.py",
        "code/tests/integration/__init__.py",
        "code/tests/contract/__init__.py",
    ]
    
    for init_file in init_files:
        full_path = root_path / init_file
        if not full_path.exists():
            full_path.touch()
            print(f"Created: {full_path}")

def main():
    """Main entry point for directory setup."""
    # Determine project root (parent of the script's directory)
    script_dir = Path(__file__).parent
    project_root = script_dir.parent  # Go up one level to 'code', then we want the parent of 'code'
    
    # Actually, the script is in code/, so project root is the parent of code/
    # But let's be explicit: we want to create structure relative to where this script is run from
    # The task says "under code/, data/, tests/, specs/" relative to project root
    # So we assume the script is run from the project root or we determine it from context
    
    # For safety, let's use the current working directory as the project root
    # unless we detect we're in a 'code' subdirectory
    cwd = Path.cwd()
    if (cwd / "code").exists():
        project_root = cwd
    else:
        # If we're running from inside code/, go up
        project_root = script_dir.parent
    
    print(f"Initializing project structure at: {project_root}")
    create_directory_structure(project_root)
    print("Project structure initialization complete.")

if __name__ == "__main__":
    main()
