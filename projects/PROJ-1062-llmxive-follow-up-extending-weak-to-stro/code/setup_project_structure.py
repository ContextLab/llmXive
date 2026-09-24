import os
import sys
from pathlib import Path
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def create_directories():
    """
    Create the project directory structure per implementation plan.
    
    Directories to create:
    - src/data/
    - src/models/
    - src/training/
    - src/analysis/
    - src/config/
    - tests/unit/
    - tests/integration/
    - contracts/
    - data/raw/
    - data/processed/
    - data/results/
    - artifacts/
    
    Note: The task description uses 'src/' but the existing API surface 
    in the project uses 'code/' as the root for source files.
    We will create directories relative to the project root, following
    the existing project structure convention (code/ instead of src/).
    """
    
    # Define directories relative to project root
    # Following the existing project convention where 'code/' is the root
    directories = [
        "code/src/data",
        "code/src/models",
        "code/src/training",
        "code/src/analysis",
        "code/src/config",
        "code/tests/unit",
        "code/tests/integration",
        "code/contracts",
        "code/data/raw",
        "code/data/processed",
        "code/data/results",
        "code/artifacts",
    ]
    
    created_count = 0
    skipped_count = 0
    
    for dir_path in directories:
        path = Path(dir_path)
        
        if path.exists() and path.is_dir():
            logger.info(f"Directory already exists: {dir_path}")
            skipped_count += 1
            continue
        
        try:
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise
    
    logger.info(f"Directory creation complete. Created: {created_count}, Skipped: {skipped_count}")
    return created_count, skipped_count

def main():
    """Main entry point for project structure setup."""
    logger.info("Starting project structure setup...")
    
    try:
        created, skipped = create_directories()
        logger.info(f"Successfully created {created} directories. {skipped} already existed.")
        return 0
    except Exception as e:
        logger.error(f"Project structure setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
