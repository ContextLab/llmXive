"""
Module to setup the required directory structure for the project.
Creates data/raw, data/processed, and data/artifacts directories.
"""
import os
import sys
from pathlib import Path
import logging

# Configure logger for this module
logger = logging.getLogger(__name__)

def setup_directories():
    """
    Create the required directory structure for the project's data artifacts.
    
    This function ensures the existence of:
    - data/raw/            : For raw downloaded data
    - data/processed/      : For cleaned and processed datasets
    - data/artifacts/      : For generated plots and intermediate artifacts
    - data/models/         : For saved model binaries (required by downstream tasks)
    - data/results/        : For evaluation metrics and reports
    - data/reports/        : For compliance and availability reports
    
    Returns:
        bool: True if all directories were created or already existed successfully.
        
    Raises:
        OSError: If a directory cannot be created due to permissions or filesystem errors.
    """
    # Define the project root relative to this script's location
    # Assuming this script is in code/, so root is parent of code/
    project_root = Path(__file__).resolve().parent.parent
    
    required_dirs = [
        project_root / "data" / "raw",
        project_root / "data" / "processed",
        project_root / "data" / "artifacts",
        project_root / "data" / "models",
        project_root / "data" / "results",
        project_root / "data" / "reports",
        project_root / "logs",
    ]
    
    success = True
    for dir_path in required_dirs:
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Directory ensured: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            success = False
    
    if success:
        logger.info("All required data directories setup successfully.")
    else:
        logger.warning("Some directories failed to create. Check permissions.")
        
    return success

if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    setup_directories()
