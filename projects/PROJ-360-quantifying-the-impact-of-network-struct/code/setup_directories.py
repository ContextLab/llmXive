import os
import logging
from pathlib import Path

# Configure logging for directory setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_directories():
    """
    Creates the essential directory structure for the project.
    
    Creates the following directories relative to the project root:
    - data/processed/
    - models/
    - results/
    - code/
    
    Also ensures subdirectories for processed networks exist as per T001b context.
    """
    # Define the base path (project root)
    base_path = Path.cwd()
    
    # Define the directories to create
    directories = [
        base_path / "data" / "processed",
        base_path / "models",
        base_path / "results",
        base_path / "code",
        # Ensure the networks subdirectory exists as well (T001b context)
        base_path / "data" / "processed" / "networks"
    ]
    
    created_count = 0
    
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
            created_count += 1
        else:
            logger.info(f"Directory already exists: {directory}")
    
    logger.info(f"Directory setup complete. {created_count} new directories created.")
    return created_count

def main():
    """Entry point for the script."""
    setup_directories()

if __name__ == "__main__":
    main()