import os
import sys
import logging
from pathlib import Path
from utils.logging import get_logger

def setup_docs_directory(docs_path: str = "docs") -> bool:
    """
    Create the documentation directory if it does not exist.

    Args:
        docs_path: Relative path to the docs directory (default: 'docs')

    Returns:
        True if the directory exists after execution (created or pre-existing)
    """
    logger = get_logger(__name__)
    path = Path(docs_path)

    if not path.exists():
        logger.info(f"Creating documentation directory: {path}")
        try:
            path.mkdir(parents=True, exist_ok=True)
            # Create a README.md to ensure the directory is tracked by git
            readme_path = path / "README.md"
            readme_path.write_text("# Project Documentation\n\nThis directory contains project documentation.\n")
            logger.info(f"Created {readme_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {path}: {e}")
            return False
    else:
        logger.info(f"Documentation directory already exists: {path}")

    return path.is_dir()

def main():
    """Entry point for directory setup script."""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    success = setup_docs_directory()
    
    if success:
        logger = get_logger(__name__)
        logger.info("Verification: docs directory exists.")
        # Explicit verification as per task requirement
        if os.path.isdir('docs'):
            logger.info("SUCCESS: os.path.isdir('docs') returned True.")
            return 0
        else:
            logger.error("FAILURE: os.path.isdir('docs') returned False despite creation attempt.")
            return 1
    else:
        logger.error("FAILURE: Could not create docs directory.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
