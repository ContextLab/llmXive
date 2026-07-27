import os
from pathlib import Path

def setup_directories():
    """
    Creates the standard project directory structure for PROJ-118.
    This implements Task T001: Create project structure.
    
    Directories created:
    - data/raw
    - data/processed
    - code (if not already present)
    - tests
    - results
    
    Also creates .gitkeep files in data directories to ensure they
    are tracked by git even when empty.
    """
    # Determine the project root. 
    # We assume this script runs from the project root or we are in the specific project folder.
    # Based on the prompt, we are working inside projects/PROJ-118-investigating-the-neural-correlates-of-p/
    # We will create the structure relative to the current working directory.
    
    base_dir = Path.cwd()
    
    # Define the required directories
    required_dirs = [
        "data/raw",
        "data/processed",
        "code",
        "tests",
        "results"
    ]
    
    created_dirs = []
    for dir_name in required_dirs:
        dir_path = base_dir / dir_name
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(dir_path))
        else:
            print(f"Directory already exists: {dir_path}")
    
    # Create .gitkeep files in data directories to ensure they are not empty
    data_dirs = ["data/raw", "data/processed"]
    for dir_name in data_dirs:
        dir_path = base_dir / dir_name
        gitkeep_path = dir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep in {dir_path}")
        else:
            print(f".gitkeep already exists in {dir_path}")
    
    # Create __init__.py in code and tests to ensure they are treated as packages
    # (Though T006 handles code/__init__.py, we ensure tests has one if missing)
    tests_init = base_dir / "tests" / "__init__.py"
    if not tests_init.exists():
        tests_init.touch()
        print(f"Created {tests_init}")
    
    return created_dirs

def main():
    """Entry point for the setup script."""
    print("Setting up project structure for PROJ-118...")
    dirs = setup_directories()
    print(f"Successfully created directories: {dirs}")
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
