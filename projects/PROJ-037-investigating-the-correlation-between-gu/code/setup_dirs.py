import os
from pathlib import Path

def create_project_structure(base_path: str = "projects/PROJ-037-investigating-the-correlation-between-gu") -> None:
    """
    Creates the standard project directory structure for PROJ-037.
    
    Directories created:
    - data/raw
    - data/processed
    - data/outputs
    - code
    - tests
    - docs
    
    Args:
        base_path: The root directory for the project structure. Defaults to the 
                   project-specific path.
    """
    root = Path(base_path)
    root.mkdir(parents=True, exist_ok=True)
    
    # Define subdirectories relative to root
    subdirs = [
        "data/raw",
        "data/processed",
        "data/outputs",
        "code",
        "tests",
        "docs"
    ]
    
    for subdir in subdirs:
        dir_path = root / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep files to ensure empty directories are tracked by git
        (dir_path / ".gitkeep").touch()
    
    print(f"Project structure created at: {root.resolve()}")

def main():
    """Entry point for script execution."""
    create_project_structure()

if __name__ == "__main__":
    main()