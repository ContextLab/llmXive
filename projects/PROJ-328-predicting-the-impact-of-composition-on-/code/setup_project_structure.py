"""
Project Structure Initialization Script for PROJ-328.
Implements Task T001: Initialize Project Directory Structure.
"""
import os
import sys
import logging
from pathlib import Path

# Add parent directory to path if running as script
if __name__ == "__main__":
    current_dir = Path(__file__).resolve().parent
    parent_dir = current_dir.parent
    if str(parent_dir) not in sys.path:
        sys.path.insert(0, str(parent_dir))

from utils.logging_config import get_logger

# Define the required directory structure
REQUIRED_DIRS = [
    # Data directories
    "data/raw",
    "data/processed",
    "data/outputs",
    "data/config",
    "data/checksums", # For storing checksums.txt

    # Code directories
    "code/ingestion",
    "code/features",
    "code/models",
    "code/evaluation",
    "code/visualization",
    "code/utils",
    "code/tests", # Helper for internal tests if needed, though main tests/ is root

    # Test directories (Root level as per spec)
    "tests/contract",
    "tests/integration",
]

# Initialize logger
logger = get_logger(__name__)

def setup_directories(base_path: Path = None) -> bool:
    """
    Creates the required directory structure.
    Returns True if all directories were created successfully.
    """
    if base_path is None:
        base_path = Path.cwd()

    success = True
    created_count = 0

    logger.info(f"Starting directory setup at: {base_path}")

    for dir_path_str in REQUIRED_DIRS:
        full_path = base_path / dir_path_str
        
        if not full_path.exists():
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path.relative_to(base_path)}")
                created_count += 1
            except OSError as e:
                logger.error(f"Failed to create directory {full_path}: {e}")
                success = False
        else:
            logger.debug(f"Directory already exists: {full_path.relative_to(base_path)}")

    # Create placeholder __init__.py files to ensure they are Python packages
    # This is critical for imports to work correctly in the pipeline
    init_files = []
    for dir_path_str in REQUIRED_DIRS:
        full_path = base_path / dir_path_str
        init_file = full_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            init_files.append(str(init_file.relative_to(base_path)))
            logger.info(f"Created init file: {init_file.relative_to(base_path)}")

    logger.info(f"Directory setup complete. Created {created_count} new directories and {len(init_files)} __init__.py files.")
    return success

def verify_directory_structure(base_path: Path = None) -> bool:
    """
    Verifies that all required directories exist.
    Returns True if all directories exist, False otherwise.
    """
    if base_path is None:
        base_path = Path.cwd()

    all_exist = True
    logger.info("Verifying directory structure...")

    for dir_path_str in REQUIRED_DIRS:
        full_path = base_path / dir_path_str
        if not full_path.is_dir():
            logger.error(f"Missing directory: {full_path.relative_to(base_path)}")
            all_exist = False
        else:
            logger.debug(f"Verified: {full_path.relative_to(base_path)}")

    if all_exist:
        logger.info("All required directories verified successfully.")
    else:
        logger.error("Verification failed: Some directories are missing.")

    return all_exist

def main():
    """
    Main entry point for the script.
    Creates directories and verifies the structure.
    """
    base_path = Path.cwd()
    logger.info(f"Running project structure setup from: {base_path}")

    # Step 1: Setup
    if not setup_directories(base_path):
        logger.critical("Failed to create all directories. Exiting.")
        sys.exit(1)

    # Step 2: Verification
    if not verify_directory_structure(base_path):
        logger.critical("Directory structure verification failed. Exiting.")
        sys.exit(1)

    logger.info("Project structure initialization (T001) completed successfully.")
    sys.exit(0)

if __name__ == "__main__":
    main()
