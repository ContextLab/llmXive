import os
import logging
from pathlib import Path
from typing import List
from config import get_config
from code.utils.logger import get_pipeline_logger

def create_data_directories() -> List[Path]:
    """
    Creates the required data directory structure for the project.
    
    Directories created:
    - data/raw: For raw, unprocessed data fetched from external sources
    - data/processed: For cleaned and feature-engineered data
    - data/results: For model outputs, validation results, and analysis artifacts
    - data/external: For external literature data and third-party datasets
    
    Returns:
        List[Path]: List of created directory paths
    """
    config = get_config()
    base_dir = Path(config.get('project_root', '.'))
    data_dir = base_dir / 'data'
    
    required_dirs = [
        'raw',
        'processed', 
        'results',
        'external'
    ]
    
    created_dirs = []
    logger = get_pipeline_logger()
    
    for dir_name in required_dirs:
        dir_path = data_dir / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            logger.info(f"Created directory: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise
    
    return created_dirs

def main():
    """Entry point for creating data directories."""
    logger = get_pipeline_logger()
    logger.info("Starting data directory creation...")
    
    try:
        created_dirs = create_data_directories()
        logger.info(f"Successfully created {len(created_dirs)} data directories:")
        for dir_path in created_dirs:
            logger.info(f"  - {dir_path}")
    except Exception as e:
        logger.error(f"Failed to create data directories: {e}")
        raise

if __name__ == '__main__':
    main()