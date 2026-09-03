import os
import sys
import logging

# Configure logging for the setup process
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def main():
    """
    Creates the required project directory structure.
    
    Creates the following directories relative to the project root:
    - data/raw
    - data/processed
    - code (already exists as this script is in it, but ensures parent structure)
    - tests
    - code/contracts
    
    This script is idempotent; it will not fail if directories already exist.
    """
    # Define the base path as the current working directory (project root)
    # Since this script is in 'code/', we go up one level to ensure we are at root
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    
    directories = [
        os.path.join(base_dir, 'data', 'raw'),
        os.path.join(base_dir, 'data', 'processed'),
        os.path.join(base_dir, 'tests'),
        os.path.join(base_dir, 'code', 'contracts')
    ]
    
    logger.info(f"Ensuring project structure exists at: {base_dir}")
    
    created_count = 0
    for directory in directories:
        if not os.path.exists(directory):
            os.makedirs(directory)
            logger.info(f"Created directory: {directory}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {directory}")
    
    if created_count > 0:
        logger.info(f"Successfully created {created_count} new directories.")
    else:
        logger.info("All required directories already existed.")
    
    # Verify structure
    missing = []
    for directory in directories:
        if not os.path.isdir(directory):
            missing.append(directory)
    
    if missing:
        logger.error(f"Failed to create or verify directories: {missing}")
        sys.exit(1)
    
    logger.info("Project structure verification complete.")

if __name__ == '__main__':
    main()
