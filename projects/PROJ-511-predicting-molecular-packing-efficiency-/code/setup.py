"""
Setup script to create the project directory structure.

This script creates the required directories for the molecular packing
efficiency prediction project and verifies their existence.

Required directories:
- code/
- data/
- data/raw_cif/
- models/
- results/
- contracts/
- specs/
"""

import os
import sys
import logging
from pathlib import Path
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Define required directories relative to project root
REQUIRED_DIRS: List[str] = [
    'code',
    'data',
    'data/raw_cif',
    'models',
    'results',
    'contracts',
    'specs'
]

def create_directories(base_path: Path = None) -> bool:
    """
    Create all required directories if they don't exist.
    
    Args:
        base_path: Base path for directory creation. Defaults to current working directory.
        
    Returns:
        True if all directories were created successfully, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    logger.info(f"Creating directories in: {base_path}")
    
    success = True
    for dir_name in REQUIRED_DIRS:
        dir_path = base_path / dir_name
        try:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            else:
                logger.info(f"Directory already exists: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            success = False
    
    return success

def verify_directories(base_path: Path = None) -> bool:
    """
    Verify that all required directories exist.
    
    Args:
        base_path: Base path to check. Defaults to current working directory.
        
    Returns:
        True if all directories exist, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()
    
    logger.info("Verifying directory structure...")
    
    all_exist = True
    for dir_name in REQUIRED_DIRS:
        dir_path = base_path / dir_name
        if dir_path.exists() and dir_path.is_dir():
            logger.info(f"✓ Verified: {dir_path}")
        else:
            logger.error(f"✗ Missing: {dir_path}")
            all_exist = False
    
    return all_exist

def main():
    """Main entry point for the setup script."""
    logger.info("=" * 60)
    logger.info("Starting project setup...")
    logger.info("=" * 60)
    
    # Create directories
    if not create_directories():
        logger.error("Failed to create some directories. Exiting.")
        sys.exit(1)
    
    logger.info("-" * 60)
    
    # Verify directories
    if not verify_directories():
        logger.error("Directory verification failed. Some directories are missing.")
        sys.exit(1)
    
    logger.info("=" * 60)
    logger.info("Project setup completed successfully!")
    logger.info("=" * 60)
    
    # Print summary
    print("\nProject structure created:")
    for dir_name in REQUIRED_DIRS:
        print(f"  - {dir_name}/")

if __name__ == '__main__':
    main()