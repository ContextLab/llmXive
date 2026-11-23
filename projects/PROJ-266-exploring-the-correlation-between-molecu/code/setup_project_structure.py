import logging
import sys
from pathlib import Path
from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

def create_directories(project_root: Path) -> None:
    """
    Create the required directory structure for the project.
    
    Requirement: Execute mkdir -p code tests data data/raw data/processed state/projects state/pending
    at the repository root.
    """
    dirs_to_create = [
        project_root / "code",
        project_root / "tests",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "state" / "projects",
        project_root / "state" / "pending",
    ]
    
    for directory in dirs_to_create:
        directory.mkdir(parents=True, exist_ok=True)
        logging.info(f"Created directory: {directory}")

def verify_directories(project_root: Path) -> None:
    """
    Verify that all required directories exist.
    
    Requirement: Verify creation by checking that each directory exists.
    """
    dirs_to_verify = [
        project_root / "code",
        project_root / "tests",
        project_root / "data",
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "state" / "projects",
        project_root / "state" / "pending",
    ]
    
    for directory in dirs_to_verify:
        if not directory.exists():
            raise FileNotFoundError(f"Required directory does not exist: {directory}")
        if not directory.is_dir():
            raise NotADirectoryError(f"Path exists but is not a directory: {directory}")
        logging.info(f"Verified directory: {directory}")

def main() -> None:
    """
    Main entry point for project structure setup and verification.
    """
    configure_root_logger()
    logger = get_logger(__name__)
    
    project_root = get_project_root()
    logger.info(f"Project root: {project_root}")
    
    logger.info("Creating project directories...")
    create_directories(project_root)
    
    logger.info("Verifying project directories...")
    verify_directories(project_root)
    
    logger.info("Project structure setup and verification complete.")

if __name__ == "__main__":
    main()