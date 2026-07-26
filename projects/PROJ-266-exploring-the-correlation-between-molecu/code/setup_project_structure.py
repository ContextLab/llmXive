import os
import sys
from pathlib import Path
from typing import List

def get_project_root() -> Path:
    """
    Determine the project root directory.
    Assumes the script is run from the project root or a subdirectory.
    """
    # Look for a marker file or specific directory structure to identify root
    # Here we assume the script is run from the root, so we use the current working directory
    # In a more robust setup, you might look for a specific file like 'pyproject.toml' or 'README.md'
    current_dir = Path.cwd()
    return current_dir

def create_directory_structure(root: Path) -> List[Path]:
    """
    Create the standard project directory structure.
    
    Args:
        root: The project root directory.
        
    Returns:
        A list of created directory paths.
    """
    # Define the directories to create relative to the project root
    directories = [
        "code",
        "tests",
        "data",
        "data/raw",
        "data/processed",
        "state",
        "state/projects",
        "specs",
        "specs/001-molecular-flexibility-permeability",
        "specs/001-molecular-flexibility-permeability/contracts",
        "figures",
    ]
    
    created_dirs = []
    for dir_path in directories:
        full_path = root / dir_path
        if not full_path.exists():
            os.makedirs(full_path, exist_ok=True)
            created_dirs.append(full_path)
            print(f"Created directory: {full_path}")
        else:
            print(f"Directory already exists: {full_path}")
            
    return created_dirs

def main():
    """Main entry point for the script."""
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    
    logger.info("Starting project structure creation...")
    root = get_project_root()
    logger.info(f"Project root identified as: {root}")
    
    created_dirs = create_directory_structure(root)
    
    if created_dirs:
        logger.info(f"Successfully created {len(created_dirs)} new directories.")
    else:
        logger.info("No new directories were created; structure already exists.")
        
    logger.info("Project structure setup complete.")

if __name__ == "__main__":
    main()
