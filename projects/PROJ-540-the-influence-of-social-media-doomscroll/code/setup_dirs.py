import os
import sys
from pathlib import Path
import logging

# Configure basic logging if not already configured
if not logging.root.handlers:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s'
    )
logger = logging.getLogger(__name__)

def create_directories():
    """
    Creates the required directory structure for the project.
    
    Directories created:
    - data/raw/
    - data/processed/
    - code/ (if not exists)
    - outputs/
    - tests/
    """
    # Define the project root relative to this script's location
    # Assuming this script is in code/, root is one level up
    project_root = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "code",
        project_root / "outputs",
        project_root / "tests"
    ]
    
    created_count = 0
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")
    
    logger.info(f"Directory setup complete. {created_count} new directories created.")
    return True

if __name__ == "__main__":
    create_directories()