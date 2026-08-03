import os
import sys
from pathlib import Path
import logging

# Configure logging for the setup process
def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)

def create_directories(base_path: Path, directories: list):
    """
    Creates the specified directories under the base_path.
    
    Args:
        base_path (Path): The root directory for the project.
        directories (list): List of relative directory paths to create.
    """
    logger = logging.getLogger(__name__)
    created_count = 0
    
    for dir_name in directories:
        dir_path = base_path / dir_name
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
                created_count += 1
            else:
                logger.info(f"Directory already exists: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise e
    
    logger.info(f"Successfully created {created_count} directories.")

def main():
    """
    Main entry point for setting up the project data directory structure.
    Creates the following directories relative to the project root:
    - data/raw/
    - data/derived/
    - data/processed/
    """
    logger = setup_logging()
    logger.info("Starting data directory structure setup...")

    # Determine the project root (assuming script is in code/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent

    # Define the required directories relative to project root
    required_dirs = [
        "data/raw",
        "data/derived",
        "data/processed"
    ]

    try:
        create_directories(project_root, required_dirs)
        logger.info("Data directory structure setup completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
