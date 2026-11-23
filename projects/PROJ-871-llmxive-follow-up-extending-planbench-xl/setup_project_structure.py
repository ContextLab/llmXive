"""
Script to initialize the project directory structure for llmXive.
This script creates the root directory and all necessary subdirectories
as defined in the project plan.
"""
import os
from pathlib import Path

def main():
    # Define the project root
    project_root = Path("projects/PROJ-871-llmxive-follow-up-extending-planbench-xl")
    
    # Define directory structure based on plan.md
    directories = [
        # Code structure
        project_root / "code",
        project_root / "code" / "utils",
        project_root / "code" / "agents",
        project_root / "code" / "dataset",
        project_root / "code" / "analysis",
        
        # Data structure
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "derived",
        project_root / "data" / "logs",
        project_root / "data" / "results",
        project_root / "data" / "figures",
        
        # Tests structure
        project_root / "tests",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
    ]
    
    # Create directories
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")
    
    # Create __init__.py files for Python packages
    init_files = [
        project_root / "code" / "__init__.py",
        project_root / "code" / "utils" / "__init__.py",
        project_root / "code" / "agents" / "__init__.py",
        project_root / "code" / "dataset" / "__init__.py",
        project_root / "code" / "analysis" / "__init__.py",
        project_root / "tests" / "__init__.py",
        project_root / "tests" / "unit" / "__init__.py",
        project_root / "tests" / "integration" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created __init__.py: {init_file}")
        else:
            print(f"__init__.py already exists: {init_file}")
    
    # Create .gitkeep files for data directories
    gitkeep_files = [
        project_root / "data" / ".gitkeep",
        project_root / "data" / "raw" / ".gitkeep",
        project_root / "data" / "derived" / ".gitkeep",
        project_root / "data" / "logs" / ".gitkeep",
        project_root / "data" / "results" / ".gitkeep",
        project_root / "data" / "figures" / ".gitkeep",
        project_root / "code" / ".gitkeep",
        project_root / "tests" / ".gitkeep",
    ]
    
    for gitkeep in gitkeep_files:
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep: {gitkeep}")
        else:
            print(f".gitkeep already exists: {gitkeep}")
    
    print(f"\nProject structure initialized at: {project_root}")

if __name__ == "__main__":
    main()