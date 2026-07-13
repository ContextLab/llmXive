"""
Script to create the required code subdirectories for the llmXive project.
Creates: code/, code/agents, code/dataset, code/analysis, code/utils
"""
import os
from pathlib import Path

def main():
    # Define the project root (assuming this script runs from the project root)
    # If run from code/, we need to go up one level
    project_root = Path(__file__).resolve().parent.parent
    code_dir = project_root / "code"
    
    # Define subdirectories to create
    subdirs = [
        "agents",
        "dataset",
        "analysis",
        "utils"
    ]
    
    # Create base code directory if it doesn't exist
    code_dir.mkdir(parents=True, exist_ok=True)
    print(f"Ensured directory exists: {code_dir}")
    
    # Create subdirectories
    for subdir in subdirs:
        subdir_path = code_dir / subdir
        subdir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {subdir_path}")
    
    # Create __init__.py files to make them proper Python packages
    init_file = code_dir / "__init__.py"
    init_file.touch(exist_ok=True)
    print(f"Created package init: {init_file}")
    
    for subdir in subdirs:
        subdir_path = code_dir / subdir
        init_subfile = subdir_path / "__init__.py"
        init_subfile.touch(exist_ok=True)
        print(f"Created package init: {init_subfile}")
    
    print("Code subdirectory structure created successfully.")

if __name__ == "__main__":
    main()