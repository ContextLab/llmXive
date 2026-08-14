import os
import sys
from pathlib import Path

def setup_data_directories(base_path: Path) -> None:
    """
    Create the required data directory structure for the project.
    
    Directories created:
    - data/raw/
    - data/processed/
    - data/results/
    
    Args:
        base_path: The project root directory path.
    """
    data_dirs = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
    ]
    
    for dir_path in data_dirs:
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def create_gitkeep(directory: Path) -> None:
    """
    Create a .gitkeep file in the specified directory to ensure
    the directory is tracked by git even if empty.
    
    Args:
        directory: The directory path where .gitkeep should be created.
    """
    gitkeep_path = directory / ".gitkeep"
    gitkeep_path.touch()
    print(f"Created .gitkeep in: {gitkeep_path}")

def main() -> None:
    """
    Main entry point to set up data directories and .gitkeep files.
    """
    # Determine project root relative to this script's location
    # Script is at: code/setup_data_dirs.py
    # We want to create directories at: <project_root>/data/...
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent.parent.parent.parent.parent.parent
    
    # Navigate up from code/ to project root
    # Assuming structure: projects/PROJ-.../code/setup_data_dirs.py
    # We need to go up 2 levels to reach projects/PROJ-.../
    project_root = code_dir.parent.parent 
    
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "results",
    ]
    
    print(f"Project root: {project_root}")
    print("Setting up data directories...")
    
    setup_data_directories(project_root)
    
    for dir_path in data_dirs:
        create_gitkeep(dir_path)
    
    print("Data directory setup complete.")

if __name__ == "__main__":
    main()