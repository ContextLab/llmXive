import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def create_directories(base_path: Optional[Path] = None) -> bool:
    """
    Create the core directory structure required for the project.
    
    Directories to create:
    - code/
    - data/tests/
    - docs/
    - data/raw/
    - data/processed/
    
    Args:
        base_path: The base directory for the project. Defaults to current working directory.
        
    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    # Define the directory structure relative to base_path
    directories = [
        "code",
        "data/tests",
        "docs",
        "data/raw",
        "data/processed"
    ]
    
    success = True
    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            success = False
    
    return success

def main():
    """
    Entry point for the directory setup script.
    Creates the required directory structure in the current working directory.
    """
    logger.info("Starting directory setup...")
    base_path = Path.cwd()
    logger.info(f"Base path: {base_path}")
    
    if create_directories(base_path):
        logger.info("Directory setup completed successfully.")
        # Verify creation by listing
        logger.info("Verifying directory structure:")
        for item in sorted(base_path.iterdir()):
            if item.is_dir():
                logger.info(f"  - {item.name}/")
                # List subdirectories if any
                for sub_item in sorted(item.iterdir()):
                    if sub_item.is_dir():
                        logger.info(f"      - {item.name}/{sub_item.name}/")
        return 0
    else:
        logger.error("Directory setup failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
