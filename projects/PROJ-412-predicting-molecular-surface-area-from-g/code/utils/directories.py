import os
from pathlib import Path
import logging
from typing import List
from .config import get_project_root, get_results_dir
from .logging import get_logger

def create_results_directories(logger: logging.Logger) -> List[Path]:
    """
    Create the results directory structure.
    
    Creates:
    - results/
    - results/reports/
    - results/plots/
    
    Args:
        logger: Logger instance for logging directory creation status.
        
    Returns:
        List of created Path objects.
    """
    project_root = get_project_root()
    results_dir = get_results_dir()
    
    # Ensure base results directory exists
    results_dir.mkdir(parents=True, exist_ok=True)
    logger.info(f"Created or verified base directory: {results_dir}")
    
    # Define subdirectories
    subdirs = [
        results_dir / "reports",
        results_dir / "plots"
    ]
    
    created_paths = []
    for subdir in subdirs:
        subdir.mkdir(parents=True, exist_ok=True)
        logger.info(f"Created directory: {subdir}")
        created_paths.append(subdir)
        
    return created_paths

def create_all_directories(logger: logging.Logger) -> List[Path]:
    """
    Create all project directories (results only for this task, 
    but structured to allow future expansion if needed).
    
    Args:
        logger: Logger instance.
        
    Returns:
        List of all created paths.
    """
    return create_results_directories(logger)

def main():
    """
    Main entry point for creating results directory structure.
    """
    logger = get_logger(__name__)
    logger.info("Starting results directory creation...")
    
    try:
        created_paths = create_results_directories(logger)
        logger.info(f"Successfully created {len(created_paths)} directories.")
        for p in created_paths:
            logger.info(f"  - {p}")
    except Exception as e:
        logger.error(f"Failed to create directories: {e}")
        raise

if __name__ == "__main__":
    main()