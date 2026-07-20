import os
import sys
from typing import List, Optional

def create_directory_structure(root_path: str) -> None:
    """Create the complete project directory structure.
    
    Args:
        root_path: The project root directory path.
    """
    # Define the directory structure to create
    directories = [
        "code",
        "data/raw",
        "data/generated",
        "data/results",
        "tests/unit",
        "tests/integration",
        "tests/contract",
        "scripts",
        "figures",
        "specs"
    ]
    
    for dir_path in directories:
        full_path = os.path.join(root_path, dir_path)
        os.makedirs(full_path, exist_ok=True)
        print(f"Created directory: {full_path}")

def create_gitkeep_files(root_path: str) -> None:
    """Create .gitkeep files in all data subdirectories.
    
    Args:
        root_path: The project root directory path.
    """
    data_subdirs = [
        "data/raw",
        "data/generated",
        "data/results"
    ]
    
    for subdir in data_subdirs:
        dir_path = os.path.join(root_path, subdir)
        gitkeep_path = os.path.join(dir_path, ".gitkeep")
        
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, "w") as f:
                f.write("# Git keeps this directory in version control\n")
            print(f"Created: {gitkeep_path}")
        else:
            print(f"Exists: {gitkeep_path}")

def main() -> None:
    """Main entry point for setting up the complete project structure."""
    # Determine project root (current directory)
    root_path = os.getcwd()
    print(f"Setting up project structure in: {root_path}")
    
    # Create directory structure
    create_directory_structure(root_path)
    
    # Create .gitkeep files
    create_gitkeep_files(root_path)
    
    print("Project structure setup complete.")

if __name__ == "__main__":
    main()
