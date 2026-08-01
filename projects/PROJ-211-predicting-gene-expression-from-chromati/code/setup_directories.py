import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def setup_directories(base_path: str = ".") -> None:
    """
    Creates the required directory structure for the project.
    
    Creates the following directories relative to base_path:
    - data/raw
    - data/processed
    - data/models
    - logs
    
    Args:
        base_path: The root directory where the folder structure will be created.
                   Defaults to current working directory.
    """
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/models",
        "logs"
    ]

    for dir_path in required_dirs:
        full_path = os.path.join(base_path, dir_path)
        try:
            os.makedirs(full_path, exist_ok=True)
            logger.info(f"Directory created or verified: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise

def main():
    """Entry point for the script."""
    logger.info("Starting directory setup...")
    setup_directories()
    logger.info("Directory setup complete.")

if __name__ == "__main__":
    main()