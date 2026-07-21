"""
Module for setting up project directory structure.

This module provides functions to create and manage the required directory
structure for the llmXive project, ensuring consistency across the codebase.
"""
import os
import sys
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directory(path: Path) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: Path object representing the directory to create
        
    Returns:
        True if directory exists (created or pre-existing), False on error
    """
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
            return True
        else:
            logger.debug(f"Directory already exists: {path}")
            return True
    except OSError as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False

def setup_data_directories(project_root: Path) -> bool:
    """
    Set up the data directory structure (raw and processed).
    
    Args:
        project_root: Path to the project root directory
        
    Returns:
        True if all directories were created successfully, False otherwise
    """
    data_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed"
    ]
    
    success = True
    for dir_path in data_dirs:
        if not ensure_directory(dir_path):
            success = False
    
    return success

def create_project_structure(project_root: Path) -> bool:
    """
    Create the complete project directory structure.
    
    Creates:
    - data/raw
    - data/processed
    - code
    - tests
    - results
    
    Args:
        project_root: Path to the project root directory
        
    Returns:
        True if all directories were created successfully, False otherwise
    """
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "tests",
        project_root / "results"
    ]
    
    success = True
    for dir_path in required_dirs:
        if not ensure_directory(dir_path):
            success = False
    
    if success:
        logger.info(f"Successfully created project structure in {project_root}")
    else:
        logger.error(f"Failed to create complete project structure in {project_root}")
    
    return success

def parse_args():
    """Parse command line arguments."""
    import argparse
    parser = argparse.ArgumentParser(
        description="Create project directory structure"
    )
    parser.add_argument(
        "--project-root",
        type=str,
        default=None,
        help="Path to project root. Defaults to parent of this script's directory."
    )
    return parser.parse_args()

def main():
    """Main entry point."""
    args = parse_args()
    
    # Determine project root
    if args.project_root:
        project_root = Path(args.project_root)
    else:
        # Default to parent of this script's directory
        script_dir = Path(__file__).resolve().parent
        project_root = script_dir.parent
    
    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        sys.exit(1)
    
    logger.info(f"Setting up project structure in: {project_root}")
    success = create_project_structure(project_root)
    
    sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()
