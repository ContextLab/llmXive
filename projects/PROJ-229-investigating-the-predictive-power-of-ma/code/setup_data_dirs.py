"""
Module to create the required data directory structure for the project.
Ensures data/raw, data/processed, and data/results directories exist.
"""
import os
from pathlib import Path
from config import get_config
from code.utils.logger import get_pipeline_logger
from code.utils.error_handling import handle_error, ConfigError

def create_data_directories():
    """
    Creates the standard data directory structure under the project root.
    
    Directories created:
    - data/raw: For raw, unprocessed data downloads
    - data/processed: For cleaned and feature-engineered data
    - data/results: For model outputs, metrics, and analysis reports
    
    Returns:
        bool: True if all directories were created or already existed, False on error.
    """
    logger = get_pipeline_logger()
    logger.info("Starting data directory creation...")
    
    try:
        config = get_config()
        base_dir = Path(config.get('paths', {}).get('project_root', '.'))
        data_root = base_dir / 'data'
        
        required_dirs = [
            data_root / 'raw',
            data_root / 'processed',
            data_root / 'results'
        ]
        
        for dir_path in required_dirs:
            if not dir_path.exists():
                dir_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {dir_path}")
            else:
                logger.info(f"Directory already exists: {dir_path}")
        
        logger.info("Data directory structure setup complete.")
        return True
        
    except Exception as e:
        handle_error(e, "Failed to create data directories", logger)
        return False

if __name__ == "__main__":
    success = create_data_directories()
    if success:
        print("Data directories created successfully.")
    else:
        print("Failed to create data directories. Check logs for details.")
        exit(1)
