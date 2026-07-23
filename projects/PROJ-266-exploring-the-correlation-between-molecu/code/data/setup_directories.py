"""
Script to setup the directory structure for data storage.
Creates 'data/raw/' and 'data/processed/' directories as required by T008.
"""
import logging
import sys
from pathlib import Path
from typing import List

# Import project utilities
# Note: Using absolute imports relative to project root as per standard Python practices
# The import path 'utils.config' assumes this script is run with 'code' in sys.path
try:
    from utils.config import get_project_root
except ImportError:
    # Fallback for direct execution if path setup differs
    import os
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from utils.config import get_project_root


def create_directories() -> List[Path]:
    """
    Creates the required directory structure for the project's data artifacts.
    
    Returns:
        List[Path]: A list of paths that were created or verified to exist.
    """
    logger = logging.getLogger(__name__)
    project_root = get_project_root()
    data_root = project_root / "data"
    
    required_dirs = [
        data_root / "raw",
        data_root / "processed",
        data_root / "figures" # Often needed downstream, good to have ready
    ]
    
    created_or_existing = []
    
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.debug(f"Directory already exists: {dir_path}")
        created_or_existing.append(dir_path)
        
    return created_or_existing


def main():
    """Entry point for the directory setup script."""
    # Configure logging
    from utils.logging import setup_logging_for_script
    setup_logging_for_script(__name__)
    
    logger = logging.getLogger(__name__)
    logger.info("Starting directory structure setup.")
    
    try:
        paths = create_directories()
        logger.info(f"Directory setup complete. Verified {len(paths)} directories.")
        for p in paths:
            logger.info(f"  - {p}")
    except Exception as e:
        logger.error(f"Failed to setup directories: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
