"""
Script to create and verify the 'docs/' directory structure for the project.
This task corresponds to T001c in the project plan.
"""
import os
import sys
import logging
from pathlib import Path

# Import logging configuration from the project's utils
# Using the API surface provided: code/utils/logging_config.py
try:
    from utils.logging_config import get_logger
except ImportError:
    # Fallback if utils is not in path or not yet initialized
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)
else:
    logger = get_logger("setup_docs_dir")


def ensure_directory(path: Path) -> bool:
    """
    Creates a directory if it does not exist.
    
    Args:
        path: Path object representing the directory to create.
        
    Returns:
        True if directory exists or was created successfully, False otherwise.
    """
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        else:
            logger.info(f"Directory already exists: {path}")
        return True
    except OSError as e:
        logger.error(f"Failed to create directory {path}: {e}")
        return False


def main() -> int:
    """
    Main entry point for the script.
    
    Returns:
        0 on success, 1 on failure.
    """
    # Determine project root. Assuming script is run from project root or code/
    # We look for the project root by checking for common markers or relative paths
    current_dir = Path(__file__).resolve().parent
    
    # If running from code/, go up one level
    if current_dir.name == 'code':
        project_root = current_dir.parent
    else:
        project_root = current_dir

    docs_path = project_root / "docs"
    
    logger.info(f"Project root identified at: {project_root}")
    logger.info(f"Target docs directory: {docs_path}")

    success = ensure_directory(docs_path)

    if success:
        logger.info("Task T001c completed successfully: 'docs/' directory created/verified.")
        return 0
    else:
        logger.error("Task T001c failed: Could not create 'docs/' directory.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
