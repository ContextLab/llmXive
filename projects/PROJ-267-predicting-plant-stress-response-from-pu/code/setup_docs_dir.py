"""
Script to create and initialize the `docs/` directory structure.
Ensures the directory exists and is writable, preparing it for
deviation logs, research notes, and pipeline documentation.
"""
import os
import sys
from pathlib import Path

# Attempt to import logging config from utils, fallback to basic config if missing
try:
    from utils.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    import logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    logger = logging.getLogger(__name__)

def ensure_directory(path_str: str) -> bool:
    """
    Creates a directory at the given path if it does not exist.
    
    Args:
        path_str: Relative or absolute path to the directory.
        
    Returns:
        True if the directory exists (created or pre-existing), False on failure.
    """
    try:
        path = Path(path_str)
        # Create parent directories if necessary
        path.mkdir(parents=True, exist_ok=True)
        
        # Verify writability by attempting to create a temporary marker file
        marker = path / ".write_test"
        marker.touch()
        marker.unlink()
        
        logger.info(f"Directory verified and writable: {path.resolve()}")
        return True
    except PermissionError:
        logger.error(f"Permission denied creating directory: {path_str}")
        return False
    except Exception as e:
        logger.error(f"Failed to create directory {path_str}: {e}")
        return False

def main() -> int:
    """
    Main entry point to create the docs directory.
    
    Returns:
        0 on success, 1 on failure.
    """
    # Determine project root (assuming this script is in code/)
    # We need to go up one level to find the project root, then create docs/
    current_file = Path(__file__).resolve()
    project_root = current_file.parent.parent
    docs_path = project_root / "docs"
    
    logger.info(f"Project root detected at: {project_root}")
    logger.info(f"Target docs directory: {docs_path}")
    
    if ensure_directory(str(docs_path)):
        logger.info("T001c: Successfully created/verified docs/ directory.")
        return 0
    else:
        logger.error("T001c: Failed to create docs/ directory.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
