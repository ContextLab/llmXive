"""
Setup script to create the required data directory structure for the llmXive project.

This script creates the following directories under the 'data/' folder:
- raw: For original, unprocessed data downloads (Sentinel-2, LiDAR)
- processed: For aligned, patched, and degraded data
- interim: For intermediate processing steps
- results: For final metrics, logs, and visualizations
"""
import os
import sys
from pathlib import Path
import logging

# Configure logging for the setup script
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directory_structure(project_root: Path) -> None:
    """
    Create the standard data directory structure.
    
    Args:
        project_root: The root directory of the project (parent of 'data/')
    """
    data_root = project_root / "data"
    
    # Define the required subdirectories
    subdirs = [
        "raw",
        "processed",
        "interim",
        "results"
    ]
    
    created_dirs = []
    for subdir in subdirs:
        dir_path = data_root / subdir
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            logger.info(f"Created directory: {dir_path}")
        except PermissionError:
            logger.error(f"Permission denied when creating directory: {dir_path}")
            raise
        except Exception as e:
            logger.error(f"Unexpected error creating directory {dir_path}: {e}")
            raise
    
    # Create a .gitkeep file in each directory to ensure they are tracked by git
    # even if they are empty
    for dir_path in created_dirs:
        gitkeep_path = dir_path / ".gitkeep"
        try:
            gitkeep_path.touch(exist_ok=True)
            logger.debug(f"Created .gitkeep in {dir_path}")
        except Exception as e:
            logger.warning(f"Could not create .gitkeep in {dir_path}: {e}")

def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        0 on success, 1 on failure
    """
    # Determine project root (assuming this script is in code/)
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    
    logger.info(f"Project root detected at: {project_root}")
    
    try:
        create_directory_structure(project_root)
        logger.info("Data directory structure created successfully.")
        return 0
    except Exception as e:
        logger.error(f"Failed to create data directory structure: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())