"""
Project Structure Setup Module.

This module is responsible for creating the foundational directory hierarchy
required for the llmXive automated science pipeline project.

It creates the following directories relative to the project root:
- code/
- data/raw/
- data/processed/
- tests/
- specs/ (if not present, though typically pre-existing)
- docs/ (if not present)

Usage:
    python code/setup_project.py
"""
import os
from pathlib import Path
import logging

# Configure logging for the module
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_project_structure(root_dir: Optional[Path] = None) -> bool:
    """
    Creates the standard project directory structure.
    
    Args:
        root_dir: The root directory of the project. Defaults to the current 
                  working directory if None.
    
    Returns:
        True if all directories were created or already existed successfully,
        False if any error occurred.
    """
    if root_dir is None:
        root_dir = Path.cwd()
    
    # Define the required directory structure
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "tests",
        "docs",
        "specs"
    ]
    
    success = True
    
    for dir_path in required_dirs:
        full_path = root_dir / dir_path
        try:
            # create_parents=True ensures parent directories are created if needed
            # exist_ok=True prevents errors if the directory already exists
            full_path.mkdir(parents=True, exist_ok=True)
            
            # Create .gitkeep files to ensure directories are tracked by git
            # even if they are empty
            gitkeep_path = full_path / ".gitkeep"
            if not gitkeep_path.exists():
                gitkeep_path.write_text("# Keep this directory in git\n")
                logger.info(f"Created directory: {full_path} with .gitkeep")
            else:
                logger.info(f"Directory already exists: {full_path}")
                
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            success = False
        except Exception as e:
            logger.error(f"Unexpected error creating directory {full_path}: {e}")
            success = False
    
    return success

def main():
    """
    Entry point for the script. Creates the project structure in the current directory.
    """
    logger.info("Starting project structure setup...")
    root = Path.cwd()
    logger.info(f"Project root: {root}")
    
    success = create_project_structure(root)
    
    if success:
        logger.info("Project structure setup completed successfully.")
        # List the created structure for verification
        logger.info("Created directories:")
        for item in sorted(root.iterdir()):
            if item.is_dir():
                logger.info(f"  - {item.name}")
        return 0
    else:
        logger.error("Project structure setup failed.")
        return 1

if __name__ == "__main__":
    exit(main())
