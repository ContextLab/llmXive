import os
import sys
from pathlib import Path

def create_directory_structure(root_path: Path) -> None:
    """
    Initialize the project directory structure for llmXive.
    
    Creates the following hierarchy relative to root_path:
    - code/
    - data/
      - raw/
      - processed/
      - interim/
    - tests/
      - unit/
      - contract/
      - integration/
    - docs/
      - contracts/
    """
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/interim",
        "tests/unit",
        "tests/contract",
        "tests/integration",
        "docs/contracts",
    ]

    for dir_path in directories:
        full_path = root_path / dir_path
        full_path.mkdir(parents=True, exist_ok=True)
        # Create .gitkeep files to ensure directories are tracked by git
        (full_path / ".gitkeep").touch()
    
    # Create specific files required by the project structure
    (root_path / "code" / "requirements.txt").touch()
    (root_path / "code" / "config.py").touch()
    
    print(f"Project structure initialized at: {root_path}")

def main() -> None:
    """Entry point for the setup script."""
    # Determine the project root. 
    # Based on task description: "in projects/PROJ-867-llmxive-follow-up-extending-representati/"
    # We assume the script is run from the repository root or the project root is passed.
    # For safety, we check if we are inside the specific project folder.
    
    current_dir = Path.cwd()
    project_name = "PROJ-867-llmxive-follow-up-extending-representati"
    
    # Check if current dir is the project root or inside it
    if current_dir.name == project_name:
        root = current_dir
    else:
        # Look for the project folder in parent directories or assume current is root if it matches
        # If running from repo root, we might need to navigate into the project folder.
        # However, standard practice for these tasks is that the working directory IS the project root.
        # We will assume the current working directory is the intended project root.
        root = current_dir
    
    create_directory_structure(root)

if __name__ == "__main__":
    main()
