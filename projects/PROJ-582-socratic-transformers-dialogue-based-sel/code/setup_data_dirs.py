import os
import sys
from pathlib import Path

def setup_data_directories(base_dir: Path) -> None:
    """
    Create the required data directory structure:
    - data/raw/
    - data/processed/
    - data/results/

    Args:
        base_dir: The root directory where the 'data' folder will be created.
    """
    data_dir = base_dir / "data"
    subdirs = ["raw", "processed", "results"]

    for subdir in subdirs:
        dir_path = data_dir / subdir
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"Created directory: {dir_path}")

def create_gitkeep(base_dir: Path) -> None:
    """
    Create .gitkeep files in each data subdirectory to ensure they are tracked
    by git even when empty.

    Args:
        base_dir: The root directory where the 'data' folder resides.
    """
    data_dir = base_dir / "data"
    subdirs = ["raw", "processed", "results"]

    for subdir in subdirs:
        gitkeep_path = data_dir / subdir / ".gitkeep"
        gitkeep_path.touch()
        print(f"Created .gitkeep: {gitkeep_path}")

def main() -> None:
    """
    Main entry point to setup data directories and .gitkeep files.
    Assumes the script is run from the project root or code directory.
    """
    # Determine the project root based on the script location
    # The script is located in: projects/PROJ-582-socratic-transformers-dialogue-based-sel/code/setup_data_dirs.py
    # We want to create data dirs relative to the project root:
    # projects/PROJ-582-socratic-transformers-dialogue-based-sel/
    current_file = Path(__file__).resolve()
    code_dir = current_file.parent
    project_root = code_dir.parent

    print(f"Project root detected at: {project_root}")
    print("Setting up data directory structure...")

    setup_data_directories(project_root)
    create_gitkeep(project_root)

    print("Data directory setup complete.")

if __name__ == "__main__":
    main()