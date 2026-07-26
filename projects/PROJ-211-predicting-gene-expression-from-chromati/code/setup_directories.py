"""
Setup directory structure for the project.
Creates necessary directories for data, models, logs, and tests.
"""
import os
import sys
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def setup_directories(base_path: str = None) -> None:
    """
    Create the required directory structure for the project.
    
    Args:
        base_path: Base project path. If None, uses current working directory.
    """
    if base_path is None:
        base_path = os.getcwd()
    
    # Define directory structure relative to base_path
    directories = [
        'data/raw',
        'data/processed',
        'data/models',
        'logs',
        'tests/contract',
        'tests/integration',
        'tests/unit',
        'docs',
        'contracts',
        'specs/001-gene-regulation/contracts'
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = os.path.join(base_path, dir_path)
        if not os.path.exists(full_path):
            os.makedirs(full_path)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {full_path}")
    
    logger.info(f"Setup complete. Created {created_count} new directories.")

def main():
    """Main entry point for directory setup."""
    logger.info("Starting directory setup...")
    setup_directories()
    logger.info("Directory setup finished.")

if __name__ == '__main__':
    main()