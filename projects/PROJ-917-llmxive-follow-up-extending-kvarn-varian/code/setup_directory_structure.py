"""
Script to create the required directory structure for the llmXive project.
Creates code/, data/, tests/, and state/ directories with their subdirectories.
"""
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

def create_directories(base_path: Path = None) -> bool:
    """
    Create the required directory structure for the project.

    Args:
        base_path: Base path for the project. Defaults to current directory.

    Returns:
        bool: True if all directories were created successfully, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()

    # Define directory structure relative to base_path
    directories = [
        # Code structure
        "code/data_generation",
        "code/model_training",
        "code/simulation",
        "code/analysis",
        "code/tests",
        "code/tests/test_data_generation",
        "code/tests/test_model_training",
        "code/tests/test_simulation",
        "code/tests/test_analysis",
        
        # Data structure
        "data/generated",
        "data/models",
        "data/simulation",
        "data/analysis",
        
        # State structure (for checksums, logs, etc.)
        "state",
    ]

    created_count = 0
    failed_count = 0

    for dir_path in directories:
        full_path = base_path / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
                created_count += 1
            else:
                logger.debug(f"Directory already exists: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            failed_count += 1

    if failed_count > 0:
        logger.warning(f"Completed with {failed_count} failures out of {len(directories)} directories.")
        return False

    logger.info(f"Successfully created {created_count} directories.")
    return True

def verify_structure(base_path: Path = None) -> bool:
    """
    Verify that all required directories exist.

    Args:
        base_path: Base path for the project. Defaults to current directory.

    Returns:
        bool: True if all directories exist, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()

    required_directories = [
        "code/data_generation",
        "code/model_training",
        "code/simulation",
        "code/analysis",
        "code/tests",
        "code/tests/test_data_generation",
        "code/tests/test_model_training",
        "code/tests/test_simulation",
        "code/tests/test_analysis",
        "data/generated",
        "data/models",
        "data/simulation",
        "data/analysis",
        "state",
    ]

    all_exist = True
    for dir_path in required_directories:
        full_path = base_path / dir_path
        if not full_path.is_dir():
            logger.error(f"Missing required directory: {full_path}")
            all_exist = False
        else:
            logger.debug(f"Verified directory: {full_path}")

    return all_exist

def main():
    """Main entry point for directory structure setup."""
    logger.info("Starting directory structure setup...")
    
    base_path = Path.cwd()
    logger.info(f"Base path: {base_path}")
    
    success = create_directories(base_path)
    
    if success:
        logger.info("Verifying directory structure...")
        if verify_structure(base_path):
            logger.info("All required directories verified successfully.")
            return 0
        else:
            logger.error("Directory verification failed.")
            return 1
    else:
        logger.error("Directory creation failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())