import os
import logging
from pathlib import Path
from typing import List
from .config import get_project_root
from .logging import get_logger

logger = get_logger(__name__)

def create_all_directories() -> List[str]:
    """
    Initialize code, tests, and results directories as specified in T001a.
    
    Creates the following directories relative to the project root:
    - code/, code/data/, code/models/, code/eval/, code/utils/
    - tests/contract/, tests/unit/, tests/integration/
    - results/reports/, results/plots/, results/baseline/, results/predictions/
    - logs/
    
    Returns:
        List[str]: List of created directory paths.
    """
    project_root = get_project_root()
    
    directories_to_create = [
        "code",
        "code/data",
        "code/models",
        "code/eval",
        "code/utils",
        "tests/contract",
        "tests/unit",
        "tests/integration",
        "results/reports",
        "results/plots",
        "results/baseline",
        "results/predictions",
        "logs",
    ]
    
    created_paths = []
    
    for dir_path in directories_to_create:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {full_path}")
            created_paths.append(str(full_path))
        else:
            logger.debug(f"Directory already exists: {full_path}")
            
    return created_paths

def create_results_directories() -> List[str]:
    """
    Create only the results subdirectories.
    
    Returns:
        List[str]: List of created results directory paths.
    """
    project_root = get_project_root()
    
    results_dirs = [
        "results/reports",
        "results/plots",
        "results/baseline",
        "results/predictions",
    ]
    
    created_paths = []
    
    for dir_path in results_dirs:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created results directory: {full_path}")
            created_paths.append(str(full_path))
        else:
            logger.debug(f"Results directory already exists: {full_path}")
            
    return created_paths

def main():
    """Entry point for directory creation script."""
    logger.info("Starting directory initialization (T001a)...")
    created = create_all_directories()
    logger.info(f"Successfully created {len(created)} directories.")
    for path in created:
        logger.info(f"  - {path}")
    return created

if __name__ == "__main__":
    main()
