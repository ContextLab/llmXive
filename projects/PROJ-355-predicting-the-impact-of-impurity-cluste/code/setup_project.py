import os
import sys
from pathlib import Path

def ensure_directory(directory: Path) -> None:
    """
    Ensure the specified directory exists. If it does not, create it.
    
    Args:
        directory (Path): The path to the directory to ensure.
    """
    directory.mkdir(parents=True, exist_ok=True)

def create_gitkeep(gitkeep_path: Path) -> None:
    """
    Create a .gitkeep file in the specified directory to ensure it is tracked by git.
    
    Args:
        gitkeep_path (Path): The path to the .gitkeep file to create.
    """
    # Create an empty file
    gitkeep_path.touch(exist_ok=True)

def main():
    """
    Main entry point for setup_project module.
    This is primarily used as an importable utility, but can be run directly.
    """
    print("setup_project module loaded successfully.")
    print("Use ensure_directory() and create_gitkeep() to manage project structure.")

if __name__ == "__main__":
    main()