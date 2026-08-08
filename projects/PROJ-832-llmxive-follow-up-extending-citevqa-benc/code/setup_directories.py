import os
import sys
from pathlib import Path

def create_directory_structure(root_dir: Path) -> None:
    """
    Creates the standard directory structure for the llmXive project.
    
    Directories created:
    - code/
    - tests/
    - data/
    - data/raw/
    - data/processed/
    - data/results/
    - data/logs/
    - scripts/
    
    Args:
        root_dir: The root directory relative to which folders are created.
    """
    directories = [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "data/results",
        "data/logs",
        "scripts",
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = root_dir / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_count += 1
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
    
    print(f"Directory structure setup complete. {created_count} new directories created.")

def main():
    """
    Entry point for the directory setup script.
    Creates the directory structure relative to the project root.
    """
    # Determine project root (assuming script is run from project root or code/)
    # If run from code/, go up one level. If run from root, stay.
    current_file = Path(__file__).resolve()
    if current_file.parent.name == "code":
        project_root = current_file.parent.parent
    else:
        project_root = current_file.parent
        
    print(f"Project root detected at: {project_root}")
    create_directory_structure(project_root)

if __name__ == "__main__":
    main()
