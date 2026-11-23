import os
import logging
from pathlib import Path
from typing import List
from .config import get_project_root
from .logging import get_logger

def create_all_directories() -> List[str]:
    """
    Initialize code, tests, results, and logs directories.
    Creates the following directories:
    - code/, code/data/, code/models/, code/eval/, code/utils/
    - tests/contract/, tests/unit/, tests/integration/
    - results/reports/, results/plots/, results/baseline/, results/predictions/
    - logs/
    
    Returns:
        List[str]: List of created directory paths relative to project root.
    """
    project_root = get_project_root()
    logger = get_logger()
    
    directories = [
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
        "logs"
    ]
    
    created_dirs = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.debug(f"Directory already exists: {dir_path}")
            
    return created_dirs

def create_results_directories() -> List[str]:
    """
    Initialize results and logs directories.
    Creates:
    - results/reports/, results/plots/, results/baseline/, results/predictions/
    - logs/
    
    Returns:
        List[str]: List of created directory paths.
    """
    project_root = get_project_root()
    logger = get_logger()
    
    directories = [
        "results/reports",
        "results/plots",
        "results/baseline",
        "results/predictions",
        "logs"
    ]
    
    created_dirs = []
    for dir_path in directories:
        full_path = project_root / dir_path
        if not full_path.exists():
            full_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(dir_path)
            logger.info(f"Created directory: {dir_path}")
        else:
            logger.debug(f"Directory already exists: {dir_path}")
            
    return created_dirs

def main():
    """Main entry point for directory creation."""
    logging.basicConfig(level=logging.INFO)
    created = create_all_directories()
    if created:
        print(f"Successfully created {len(created)} directories.")
    else:
        print("All required directories already exist.")

if __name__ == "__main__":
    main()