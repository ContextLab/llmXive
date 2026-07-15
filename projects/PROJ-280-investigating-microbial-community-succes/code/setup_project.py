"""
Script to initialize the project directory structure for PROJ-280.
This script creates all required directories as specified in T001a.
"""
import os
from pathlib import Path

def main():
    # Define the project root
    project_root = Path("projects/PROJ-280-investigating-microbial-community-succes")
    
    # Define the required subdirectories relative to the project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/config",
        "code",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "state/projects",
        "contracts"
    ]
    
    # Create the project root if it doesn't exist
    project_root.mkdir(parents=True, exist_ok=True)
    print(f"Ensured project root exists: {project_root}")
    
    # Create each subdirectory
    created_dirs = []
    for dir_path in required_dirs:
        full_path = project_root / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        created_dirs.append(str(full_path))
        print(f"Created directory: {full_path}")
    
    # Create __init__.py files in Python package directories to ensure they are recognized as packages
    python_pkg_dirs = ["code", "tests/unit", "tests/contract", "tests/integration"]
    for pkg_dir in python_pkg_dirs:
        init_file = project_root / pkg_dir / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            print(f"Created empty __init__.py: {init_file}")

    # Create .gitkeep files in data directories to ensure they are tracked by git
    data_dirs = ["data/raw", "data/processed", "data/config"]
    for data_dir in data_dirs:
        gitkeep = project_root / data_dir / ".gitkeep"
        if not gitkeep.exists():
            gitkeep.touch()
            print(f"Created .gitkeep: {gitkeep}")

    print(f"\nProject structure initialization complete for {project_root}")
    print(f"Total directories created/verified: {len(required_dirs)}")

if __name__ == "__main__":
    main()
