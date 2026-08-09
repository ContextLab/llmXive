"""
Directory management utilities for the project.
Handles creation and organization of project folders.
"""
import os
import logging
from pathlib import Path
from typing import List

from .config import get_project_root
from .logging import get_logger

def create_all_directories():
    """
    Create all required project directories.
    
    Creates the following directory structure:
    - code/, code/data/, code/models/, code/eval/, code/utils/
    - data/raw/, data/processed/, data/splits/, data/schemas/
    - tests/contract/, tests/unit/, tests/integration/
    - results/reports/, results/plots/, results/baseline/, results/predictions/
    - logs/
    """
    logger = get_logger(__name__)
    project_root = get_project_root()
    
    # Define all required directories relative to project root
    directories = [
        # Code structure
        "code",
        "code/data",
        "code/models",
        "code/eval",
        "code/utils",
        
        # Data structure
        "data/raw",
        "data/processed",
        "data/splits",
        "data/schemas",
        
        # Test structure
        "tests/contract",
        "tests/unit",
        "tests/integration",
        
        # Results structure
        "results/reports",
        "results/plots",
        "results/baseline",
        "results/predictions",
        
        # Logs
        "logs"
    ]
    
    created_count = 0
    for dir_path in directories:
        full_path = project_root / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created directory: {full_path}")
                created_count += 1
            else:
                logger.debug(f"Directory already exists: {full_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {full_path}: {e}")
            raise
    
    logger.info(f"Directory structure initialization complete. Created {created_count} new directories.")
    return created_count

def create_results_directories():
    """
    Create only the results-related directories.
    
    Creates:
    - results/reports/
    - results/plots/
    - results/baseline/
    - results/predictions/
    """
    logger = get_logger(__name__)
    project_root = get_project_root()
    
    results_dirs = [
        "results/reports",
        "results/plots",
        "results/baseline",
        "results/predictions"
    ]
    
    created_count = 0
    for dir_path in results_dirs:
        full_path = project_root / dir_path
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.debug(f"Created results directory: {full_path}")
                created_count += 1
        except OSError as e:
            logger.error(f"Failed to create results directory {full_path}: {e}")
            raise
    
    logger.info(f"Created {created_count} results directories.")
    return created_count

def setup_logging():
    """
    Setup logging configuration for the directory setup process.
    
    Returns:
        logging.Logger: Configured logger instance
    """
    logger = get_logger(__name__)
    return logger

def main():
    """Entry point for directory structure creation."""
    create_all_directories()
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
