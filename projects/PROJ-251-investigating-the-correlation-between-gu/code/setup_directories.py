import os
import sys
from pathlib import Path
import logging

# Configure logging for the setup process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directories():
    """
    Create the required project root directories explicitly.
    
    Directories created:
    - code/
    - data/raw
    - data/processed
    - data/results
    - tests/
    - data/research
    
    Returns:
        list: List of created directory paths as strings.
    """
    # Define the base directory (project root)
    base_dir = Path(__file__).resolve().parent.parent
    
    # Define relative paths for directories to be created
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "tests",
        "data/research"
    ]
    
    created_dirs = []
    
    for dir_path in directories:
        full_path = base_dir / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
                created_dirs.append(str(full_path))
            else:
                logger.info(f"Directory already exists: {full_path}")
                created_dirs.append(str(full_path))
        except Exception as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise
    
    return created_dirs

def main():
    """
    Main entry point for directory creation script.
    """
    logger.info("Starting directory creation process...")
    try:
        created = create_directories()
        logger.info(f"Successfully created/verified {len(created)} directories.")
        for d in created:
            logger.info(f"  - {d}")
        return 0
    except Exception as e:
        logger.error(f"Directory creation failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
