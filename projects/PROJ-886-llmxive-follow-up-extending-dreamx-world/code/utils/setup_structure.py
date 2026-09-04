import os
from pathlib import Path

def main():
    """
    Initialize the full nested directory tree for project PROJ-886.
    Creates data/raw, data/derived, code subdirectories, and test directories.
    """
    project_root = Path("projects/PROJ-886-llmxive-follow-up-extending-dreamx-world")
    
    # Define the directory structure to create
    directories = [
        "data/raw",
        "data/derived",
        "code",
        "code/models",
        "code/pipeline",
        "code/analysis",
        "code/utils",
        "tests/unit",
        "tests/integration",
        "specs"
    ]
    
    # Create directories
    for dir_path in directories:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {full_path}")
    
    # Create __init__.py files to make directories Python packages
    init_files = [
        "code/__init__.py",
        "code/models/__init__.py",
        "code/pipeline/__init__.py",
        "code/analysis/__init__.py",
        "code/utils/__init__.py",
        "tests/__init__.py",
        "tests/unit/__init__.py",
        "tests/integration/__init__.py"
    ]
    
    for init_file in init_files:
        full_path = project_root / init_file
        if not full_path.exists():
            full_path.touch()
            print(f"Created empty __init__.py: {full_path}")
        else:
            print(f"__init__.py already exists: {full_path}")
    
    # Create .gitkeep files in data directories to ensure they are tracked
    gitkeep_files = [
        "data/raw/.gitkeep",
        "data/derived/.gitkeep"
    ]
    
    for gitkeep in gitkeep_files:
        full_path = project_root / gitkeep
        if not full_path.exists():
            full_path.touch()
            print(f"Created .gitkeep: {full_path}")
    
    print(f"\nProject structure initialized at: {project_root}")
    return project_root

if __name__ == "__main__":
    main()