import os
import sys
from pathlib import Path

def create_structure():
    """
    Creates the project directory structure for PROJ-062.
    This script implements T001: Create project structure per implementation plan.
    
    It creates:
    1. The main project root: projects/PROJ-062-quantifying-the-impact-of-code-ownership/
    2. Standard source directories: code/, code/utils/, tests/, data/, etc.
    3. Configuration and documentation directories.
    """
    # Define the project root relative to the current working directory
    # Assuming this script is run from the repository root
    project_root = Path("projects/PROJ-062-quantifying-the-impact-of-code-ownership")
    
    # Define the directory structure to create
    directories = [
        # Project root itself is created by the first entry if it doesn't exist
        project_root,
        
        # Source code structure
        project_root / "code",
        project_root / "code" / "utils",
        project_root / "code" / "scripts",
        
        # Test structure
        project_root / "tests",
        project_root / "tests" / "unit",
        project_root / "tests" / "integration",
        project_root / "tests" / "contract",
        
        # Data structure (as per T004 requirements, though T004 is a separate task)
        # We create the container here, T004 will add .gitkeep files
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "intermediate",
        project_root / "data" / "results",
        project_root / "data" / "ownership_metrics",
        
        # State and configuration
        project_root / "state",
        project_root / "specs",
        project_root / "docs",
        
        # Figures output
        project_root / "figures"
    ]
    
    created_count = 0
    for dir_path in directories:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"Created directory: {dir_path}")
            created_count += 1
        else:
            print(f"Directory already exists: {dir_path}")
    
    print(f"\nProject structure creation complete. {created_count} new directories created.")
    print(f"Project root: {project_root.absolute()}")
    
    # Create __init__.py files to make directories Python packages where appropriate
    init_files = [
        project_root / "code" / "__init__.py",
        project_root / "code" / "utils" / "__init__.py",
        project_root / "code" / "scripts" / "__init__.py",
        project_root / "tests" / "__init__.py",
        project_root / "tests" / "unit" / "__init__.py",
        project_root / "tests" / "integration" / "__init__.py",
        project_root / "tests" / "contract" / "__init__.py",
    ]
    
    for init_file in init_files:
        if not init_file.exists():
            init_file.touch()
            print(f"Created init file: {init_file}")
    
    return True

def main():
    """Entry point for the script."""
    success = create_structure()
    if not success:
        sys.exit(1)

if __name__ == "__main__":
    main()
