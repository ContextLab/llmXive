import os
import sys
from pathlib import Path

def create_gitkeep(directory: Path) -> None:
    """
    Creates a .gitkeep file in the specified directory to ensure
    the directory is tracked by git even if it is empty.
    
    Args:
        directory: Path object representing the directory to create .gitkeep in.
    """
    gitkeep_path = directory / ".gitkeep"
    if not gitkeep_path.exists():
        gitkeep_path.touch()
        print(f"Created .gitkeep in {directory}")
    else:
        print(f".gitkeep already exists in {directory}")

def setup_data_directories(base_path: Path) -> None:
    """
    Creates the standard data directory structure: raw, processed, and results.
    
    Args:
        base_path: The root directory where 'data' subdirectory will be created.
    """
    data_root = base_path / "data"
    subdirs = ["raw", "processed", "results"]
    
    for subdir in subdirs:
        dir_path = data_root / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")
        create_gitkeep(dir_path)

def main() -> None:
    """
    Main entry point to execute the data directory setup.
    Determines the project root based on the script location and runs setup.
    """
    # Determine project root: script is in code/, root is parent of code/
    script_path = Path(__file__).resolve()
    project_root = script_path.parent
    
    print(f"Project root detected at: {project_root}")
    setup_data_directories(project_root)
    print("Data directory setup complete.")

if __name__ == "__main__":
    main()