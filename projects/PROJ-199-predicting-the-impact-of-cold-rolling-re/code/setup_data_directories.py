"""
Setup script for creating the required data directory structure.

This script creates the subdirectories `raw`, `processed`, and `interim`
within the project's `data/` folder, along with `.gitkeep` files to ensure
the directories are tracked by version control.
"""
import os
import logging
from pathlib import Path

# Import logging utility from the project's existing utils
try:
    from utils.logging import get_logger
except ImportError:
    # Fallback if utils.logging is not yet importable (e.g., during initial setup)
    # Set up a basic logger for this standalone execution
    logger = logging.getLogger(__name__)
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
else:
    logger = get_logger(__name__)

def setup_data_directories(base_dir: Path) -> None:
    """
    Create the standard data subdirectories and .gitkeep files.
    
    Args:
        base_dir: The project root directory (parent of 'data').
    """
    data_dir = base_dir / "data"
    subdirs = ["raw", "processed", "interim"]
    
    logger.info(f"Ensuring data directory structure exists at: {data_dir}")
    
    # Create the main data directory if it doesn't exist
    if not data_dir.exists():
        data_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created main data directory: {data_dir}")
    
    for subdir_name in subdirs:
        subdir_path = data_dir / subdir_name
        
        if not subdir_path.exists():
            subdir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created subdirectory: {subdir_path}")
        else:
            logger.debug(f"Subdirectory already exists: {subdir_path}")
        
        # Create .gitkeep file to ensure directory is tracked by git
        gitkeep_path = subdir_path / ".gitkeep"
        if not gitkeep_path.exists():
            gitkeep_path.touch()
            logger.info(f"Created .gitkeep file: {gitkeep_path}")
        else:
            logger.debug(f".gitkeep file already exists: {gitkeep_path}")

def main():
    """Main entry point for the script."""
    # Determine project root (assuming script is in code/ or code/utils/)
    # We look for the 'data' directory relative to the script location
    script_path = Path(__file__).resolve()
    # Try to find the project root by looking for 'data' or 'code'
    current = script_path.parent
    project_root = None
    
    while current != current.parent:
        if (current / "data").exists() or (current / "code").exists():
            # Check if this looks like a project root
            if (current / "tasks.md").exists() or (current / "README.md").exists() or (current / "requirements.txt").exists():
                project_root = current
                break
            # If we found data/code but no project markers, maybe we are in a subfolder
            # Let's assume the parent of 'code' is the root if 'code' exists
            if (current / "code").exists():
                project_root = current
                break
        current = current.parent
    
    if project_root is None:
        # Fallback: assume script is in code/ and root is parent
        if script_path.parent.name == "code":
            project_root = script_path.parent.parent
        else:
            project_root = script_path.parent
    
    logger.info(f"Detected project root at: {project_root}")
    
    try:
        setup_data_directories(project_root)
        logger.info("Data directory structure setup completed successfully.")
    except Exception as e:
        logger.error(f"Failed to setup data directories: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
