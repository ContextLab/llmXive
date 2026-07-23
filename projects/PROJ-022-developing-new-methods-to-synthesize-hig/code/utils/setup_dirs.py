import os
import sys
from pathlib import Path
import logging
from utils.logging_config import setup_pipeline_logger

def ensure_directory(path_str: str) -> bool:
    """
    Ensure a directory exists, creating it if necessary.
    
    Args:
        path_str: Relative or absolute path string to the directory.
        
    Returns:
        True if directory exists or was created successfully, False otherwise.
    """
    try:
        path = Path(path_str)
        path.mkdir(parents=True, exist_ok=True)
        return True
    except Exception as e:
        logging.error(f"Failed to create directory {path_str}: {e}")
        return False

def setup_project_structure() -> None:
    """
    Create the required directory structure for the project.
    
    Creates the following directories relative to the project root:
    - code/
    - data/raw
    - data/processed
    - data/reports
    - tests/
    - artifacts/
    - figures/
    """
    project_root = Path(__file__).resolve().parent.parent.parent
    
    required_dirs = [
        "code",
        "data/raw",
        "data/processed",
        "data/reports",
        "tests",
        "artifacts",
        "figures"
    ]
    
    logger = setup_pipeline_logger("setup_dirs")
    logger.info("Starting directory structure setup")
    
    for dir_name in required_dirs:
        full_path = project_root / dir_name
        if ensure_directory(str(full_path)):
            logger.info(f"Created/verified directory: {full_path}")
        else:
            logger.error(f"Failed to create directory: {full_path}")
            raise RuntimeError(f"Directory creation failed for {full_path}")
    
    logger.info("Directory structure setup completed successfully")

def main():
    """Entry point for running directory setup as a script."""
    setup_project_structure()
    print("Project directory structure created successfully.")

if __name__ == "__main__":
    main()
