import logging
import sys
from pathlib import Path
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

logger = get_logger(__name__)

def create_directories() -> None:
    """
    Create the required directory structure for the project.
    
    Requirements:
    - data/raw/
    - data/processed/
    - state/projects/
    - state/pending/
    
    Uses os.makedirs with exist_ok=True to ensure idempotency.
    """
    project_root = get_project_root()
    logger.info(f"Project root identified at: {project_root}")
    
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "state" / "projects",
        project_root / "state" / "pending",
    ]
    
    for dir_path in directories:
        logger.info(f"Creating directory: {dir_path}")
        dir_path.mkdir(parents=True, exist_ok=True)
        if not dir_path.is_dir():
            raise RuntimeError(f"Failed to create directory: {dir_path}")

def verify_directories() -> None:
    """
    Verify that the required directories exist.
    
    Raises AssertionError if any required directory is missing.
    """
    project_root = get_project_root()
    
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "state" / "projects",
    ]
    
    for dir_path in required_dirs:
        logger.info(f"Verifying directory: {dir_path}")
        assert dir_path.is_dir(), f"Directory does not exist: {dir_path}"
        logger.info(f"Verified: {dir_path}")

def main() -> None:
    """
    Main entry point for the directory setup script.
    
    1. Creates all required directories.
    2. Verifies that the directories were created successfully.
    """
    configure_root_logger()
    logger.info("Starting directory setup for T008a")
    
    try:
        create_directories()
        verify_directories()
        logger.info("Directory setup and verification completed successfully.")
    except Exception as e:
        logger.error(f"Directory setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
