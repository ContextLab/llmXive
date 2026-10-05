import os
import sys
from pathlib import Path
from config import get_project_root

def ensure_dir(dir_path: Path) -> None:
    """Ensure a directory exists, creating it if necessary."""
    dir_path.mkdir(parents=True, exist_ok=True)

def create_gitkeep(dir_path: Path) -> None:
    """Create a .gitkeep file in the specified directory."""
    gitkeep_file = dir_path / ".gitkeep"
    gitkeep_file.touch(exist_ok=True)

def create_gitignore(dir_path: Path, content: str = "*\n") -> None:
    """Create a .gitignore file in the specified directory with optional content."""
    gitignore_file = dir_path / ".gitignore"
    # Only create if it doesn't exist, or overwrite if we want to enforce specific content
    # For safety in setup, we create it if missing
    if not gitignore_file.exists():
        gitignore_file.write_text(content)

def main() -> None:
    """
    Setup data directory structure: Create data/raw, data/processed, artifacts directories
    with .gitkeep and .gitignore files in each.
    """
    project_root = get_project_root()
    
    # Define the directories to create
    data_raw = project_root / "data" / "raw"
    data_processed = project_root / "data" / "processed"
    artifacts_dir = project_root / "artifacts"
    
    directories = [data_raw, data_processed, artifacts_dir]
    
    # Gitignore content to ignore everything in these data directories
    gitignore_content = "*\n!.gitkeep\n"
    
    for directory in directories:
        print(f"Ensuring directory: {directory}")
        ensure_dir(directory)
        print(f"Creating .gitkeep in: {directory}")
        create_gitkeep(directory)
        print(f"Creating .gitignore in: {directory}")
        create_gitignore(directory, gitignore_content)
    
    print("Data directory structure setup complete.")

if __name__ == "__main__":
    main()
