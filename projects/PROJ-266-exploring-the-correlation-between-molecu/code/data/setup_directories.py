"""
Script to create and verify the required directory structure for the project.
Implements T008a: Create and verify directory structure for data/raw/, data/processed/,
state/projects/, and state/pending/.
"""
import logging
import sys
from pathlib import Path

# Add the project root to the path to allow imports of utils
# This assumes the script is run from the project root as `python code/data/setup_directories.py`
# or via `python -m code.data.setup_directories`
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from utils.logging import get_logger, configure_root_logger
from utils.config import get_project_root

def create_directories(logger: logging.Logger) -> None:
    """
    Create the required directory structure.
    Requirement: Execute os.makedirs for data/raw, data/processed, state/projects, state/pending.
    """
    base_path = get_project_root()
    
    dirs_to_create = [
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "state" / "projects",
        base_path / "state" / "pending",
    ]

    for dir_path in dirs_to_create:
        logger.info(f"Creating directory: {dir_path}")
        dir_path.mkdir(parents=True, exist_ok=True)

def verify_directories(logger: logging.Logger) -> None:
    """
    Verify that the directories were created successfully.
    Requirement: Immediately verify creation by executing assertions.
    """
    base_path = get_project_root()
    
    dirs_to_verify = [
        "data/raw",
        "data/processed",
        "state/projects",
        "state/pending",
    ]

    for rel_dir in dirs_to_verify:
        dir_path = base_path / rel_dir
        if not dir_path.is_dir():
            error_msg = f"Verification failed: Directory {dir_path} does not exist."
            logger.error(error_msg)
            raise AssertionError(error_msg)
        
        logger.info(f"Verified directory exists: {dir_path}")

def main():
    """
    Main entry point for the script.
    Creates directories and verifies them.
    """
    configure_root_logger()
    logger = get_logger("setup_directories")
    
    logger.info("Starting directory setup (Task T008a)...")
    
    try:
        create_directories(logger)
        verify_directories(logger)
        logger.info("Directory setup and verification completed successfully.")
    except Exception as e:
        logger.error(f"Directory setup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
