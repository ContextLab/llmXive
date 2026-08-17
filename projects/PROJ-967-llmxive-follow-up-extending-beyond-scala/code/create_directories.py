import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def ensure_directory(path: Path) -> None:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path: The directory path to ensure exists.
    """
    try:
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        else:
            logger.debug(f"Directory already exists: {path}")
    except PermissionError:
        logger.error(f"Permission denied creating directory: {path}")
        raise
    except Exception as e:
        logger.error(f"Error creating directory {path}: {e}")
        raise

def main() -> None:
    """
    Main function to create the required data directories for the project.
    
    Creates the following directories relative to the project root:
    - data/raw
    - data/processed
    - results
    """
    # Determine project root (assuming script is in code/)
    project_root = Path(__file__).resolve().parent.parent
    
    # Define required directories
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "results"
    ]
    
    logger.info(f"Creating directories relative to: {project_root}")
    
    for directory in directories:
        ensure_directory(directory)
    
    logger.info("All required directories created successfully.")

if __name__ == "__main__":
    main()
