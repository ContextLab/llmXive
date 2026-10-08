import os
import sys
from pathlib import Path

def create_directories(base_path: Path) -> None:
    """Create the required project directory structure."""
    subdirs = [
        "src",
        "data/raw",
        "data/processed",
        "data/results",
        "tests"
    ]
    
    for subdir in subdirs:
        dir_path = base_path / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def create_gitkeep_files(base_path: Path) -> None:
    """Create .gitkeep files in data directories to ensure they are tracked by git."""
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/results"
    ]
    
    for data_dir in data_dirs:
        file_path = base_path / data_dir / ".gitkeep"
        file_path.touch()
        print(f"Created .gitkeep: {file_path}")

def verify_structure(base_path: Path) -> bool:
    """Verify that all required directories exist."""
    required_dirs = [
        "src",
        "data/raw",
        "data/processed",
        "data/results",
        "tests"
    ]
    
    all_exist = True
    for subdir in required_dirs:
        dir_path = base_path / subdir
        if not dir_path.is_dir():
            print(f"ERROR: Directory missing: {dir_path}")
            all_exist = False
        else:
            print(f"Verified: {dir_path}")
    
    return all_exist

def main() -> int:
    """Main entry point for the setup script."""
    # Determine the project root based on the task requirements
    # The task requires creating: projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/
    # and its subdirectories relative to the project root.
    
    # We assume the script is run from the project root or we construct the path explicitly.
    # The task verification command checks: 
    # paths=['projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/src', ...]
    # So we need to create these relative to the current working directory (project root).
    
    project_root = Path.cwd()
    code_base = project_root / "projects" / "PROJ-582-socratic-transformers-dialogue-based-sel" / "code"
    
    print(f"Setting up project structure at: {code_base}")
    
    # Create the base code directory if it doesn't exist
    code_base.mkdir(parents=True, exist_ok=True)
    
    # Create subdirectories
    create_directories(code_base)
    
    # Create .gitkeep files
    create_gitkeep_files(code_base)
    
    # Verify the structure
    if verify_structure(code_base):
        print("Project structure setup complete.")
        return 0
    else:
        print("Project structure setup failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
