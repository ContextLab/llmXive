import os
import sys
from pathlib import Path


def setup_data_directories(root_dir: str) -> None:
    """
    Create the required data directory structure under the project root.
    
    Creates:
      - data/raw/
      - data/processed/
      - data/results/
    
    Args:
        root_dir: The project root directory path.
    """
    root_path = Path(root_dir)
    data_root = root_path / "data"
    
    directories = [
        data_root / "raw",
        data_root / "processed",
        data_root / "results",
    ]
    
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {directory}")


def create_gitkeep(root_dir: str) -> None:
    """
    Create .gitkeep files in all data directories to ensure they are tracked by git.
    
    Args:
        root_dir: The project root directory path.
    """
    root_path = Path(root_dir)
    data_root = root_path / "data"
    
    directories = [
        data_root / "raw",
        data_root / "processed",
        data_root / "results",
    ]
    
    for directory in directories:
        gitkeep_path = directory / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            print(f"Created .gitkeep: {gitkeep_path}")
        else:
            print(f".gitkeep already exists: {gitkeep_path}")


def main() -> None:
    """
    Main entry point to setup the data directory structure and .gitkeep files.
    Expects the project root directory as the first command-line argument.
    """
    if len(sys.argv) < 2:
        print("Usage: python data_setup.py <project_root_directory>")
        sys.exit(1)
    
    project_root = sys.argv[1]
    
    if not os.path.isdir(project_root):
        print(f"Error: Directory '{project_root}' does not exist.")
        sys.exit(1)
    
    setup_data_directories(project_root)
    create_gitkeep(project_root)
    print("Data directory setup complete.")


if __name__ == "__main__":
    main()