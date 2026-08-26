import logging
import sys
from pathlib import Path
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

def create_directories() -> None:
    """
    Create and verify the required directory structure for the project.
    
    Requirements:
    - data/raw/
    - data/processed/
    - state/projects/
    - state/pending/
    
    Verifies creation immediately after execution.
    """
    logger = get_logger(__name__)
    project_root = get_project_root()
    
    # Define the directories to create relative to project root
    directories = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "state" / "projects",
        project_root / "state" / "pending",
    ]
    
    logger.info("Creating required directory structure...")
    
    for directory in directories:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created/verified directory: {directory}")
        except OSError as e:
            logger.error(f"Failed to create directory {directory}: {e}")
            raise
    
    # Verification step: Assert existence immediately
    logger.info("Verifying directory creation...")
    
    assert project_root.joinpath("data", "raw").is_dir(), "Verification failed: data/raw does not exist"
    assert project_root.joinpath("data", "processed").is_dir(), "Verification failed: data/processed does not exist"
    assert project_root.joinpath("state", "projects").is_dir(), "Verification failed: state/projects does not exist"
    assert project_root.joinpath("state", "pending").is_dir(), "Verification failed: state/pending does not exist"
    
    logger.info("All required directories verified successfully.")

def main() -> None:
    """Entry point for directory setup script."""
    configure_root_logger()
    logger = get_logger(__name__)
    
    try:
        create_directories()
        logger.info("Directory setup completed successfully.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"Directory setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
