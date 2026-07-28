"""
Script to create the required data directory structure for the project.

This script creates:
- data/raw/
- data/processed/
- data/results/

It uses the existing logging utility and can be integrated into the main pipeline.
"""
import os
from pathlib import Path
from typing import List

# Import existing utilities from the project
from utils.logging import get_logger, info, warning, error

# Define the required directories relative to the project root
REQUIRED_DIRS: List[str] = [
    "data/raw",
    "data/processed",
    "data/results"
]

def create_data_directories(base_path: Path = None) -> List[Path]:
    """
    Create the required data directory structure.
    
    Args:
        base_path: The base project directory. Defaults to the parent of this script's directory.
        
    Returns:
        A list of Path objects for the created directories.
    """
    if base_path is None:
        # Default to the project root (parent of code/)
        base_path = Path(__file__).resolve().parent.parent
        
    logger = get_logger(__name__)
    created_paths: List[Path] = []
    
    info(logger, f"Creating data directories in: {base_path}")
    
    for dir_name in REQUIRED_DIRS:
        full_path = base_path / dir_name
        
        if full_path.exists():
            info(logger, f"Directory already exists: {full_path}")
        else:
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                created_paths.append(full_path)
                info(logger, f"Created directory: {full_path}")
            except OSError as e:
                error(logger, f"Failed to create directory {full_path}: {e}")
                raise
                
    if not created_paths:
        warning(logger, "No new directories were created; all required directories already exist.")
    else:
        info(logger, f"Successfully created {len(created_paths)} directory(ies).")
        
    return created_paths

def main():
    """Entry point for the script."""
    try:
        paths = create_data_directories()
        info(get_logger(__name__), "Data directory structure setup complete.")
        for p in paths:
            print(f"  - {p}")
    except Exception as e:
        error(get_logger(__name__), f"Error during setup: {e}")
        raise

if __name__ == "__main__":
    main()
