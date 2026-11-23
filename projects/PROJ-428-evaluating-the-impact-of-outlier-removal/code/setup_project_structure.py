import os
import sys
from pathlib import Path

def main():
    """
    Create the project structure for PROJ-428-evaluating-the-impact-of-outlier-removal.
    This script creates the necessary directory hierarchy and initializes files
    as per the implementation plan.
    """
    # Define the project root relative to the code directory
    # The task asks for structure under projects/PROJ-428-...
    # Assuming the script runs from the repository root or code/
    current_path = Path.cwd()
    
    # Determine project root (look for 'projects' or create structure relative to current)
    # Based on task description: `projects/PROJ-428-evaluating-the-impact-of-outlier-removal/`
    # We will create this structure relative to the current working directory.
    
    project_name = "PROJ-428-evaluating-the-impact-of-outlier-removal"
    project_root = current_path / "projects" / project_name
    
    # Define required directories
    directories = [
        "code",
        "code/src",
        "code/tests",
        "data/raw",
        "data/processed",
        "data/results",
        "data/results/figures",
        "state",
        "docs",
        "configs",
        "contracts"
    ]
    
    # Create directories
    for dir_name in directories:
        dir_path = project_root / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
    
    # Create __init__.py files to make directories Python packages
    init_files = [
        project_root / "code" / "__init__.py",
        project_root / "code" / "src" / "__init__.py",
        project_root / "code" / "tests" / "__init__.py"
    ]
    
    for init_file in init_files:
        init_file.touch(exist_ok=True)
        # Add a simple docstring or comment if empty
        if init_file.stat().st_size == 0:
            init_file.write_text("# Package initialization\n")
        print(f"Initialized package: {init_file}")
    
    # Create a placeholder README in the project root
    readme_path = project_root / "README.md"
    if not readme_path.exists():
        readme_content = f"""# {project_name}

## Overview
This project evaluates the impact of outlier removal methods on variance estimation.

## Structure
- `code/`: Source code and tests
- `data/`: Raw, processed, and result data
- `state/`: Checkpoints and intermediate states
- `docs/`: Documentation
- `configs/`: Configuration files
- `contracts/`: Schema contracts

## Execution
Run `python code/setup_project_structure.py` to ensure structure is correct.
"""
        readme_path.write_text(readme_content)
        print(f"Created README: {readme_path}")
    
    print(f"Project structure created successfully at: {project_root}")
    return 0

if __name__ == "__main__":
    sys.exit(main())