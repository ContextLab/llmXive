"""
Script to initialize the project data directory structure.
Creates required directories for raw data, processed data, and model artifacts.
"""
import os
from pathlib import Path
import logging

# Configure basic logging for this script
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

def setup_data_directories(project_root: Path) -> None:
    """
    Creates the standard data directory structure required by the project.
    
    Directories created:
    - data/raw/        : For raw, unprocessed datasets
    - data/processed/  : For processed, cleaned, and feature-engineered data
    - data/models/     : For saved model artifacts and checkpoints
    
    Args:
        project_root: The root path of the project where data directories will be created.
    """
    data_dirs = [
        "data/raw",
        "data/processed",
        "data/models"
    ]
    
    created_count = 0
    
    for dir_path in data_dirs:
        full_path = project_root / dir_path
        try:
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_count += 1
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise
    
    logger.info(f"Successfully created {created_count} data directories under {project_root}")

if __name__ == "__main__":
    # Determine project root (assuming script is in code/scripts/)
    script_dir = Path(__file__).resolve().parent
    project_root = script_dir.parent.parent
    
    logger.info(f"Project root detected at: {project_root}")
    setup_data_directories(project_root)
    logger.info("Data directory setup complete.")