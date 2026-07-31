import os
from pathlib import Path
import logging
from typing import List
from .config import get_project_root, get_results_dir
from .logging import get_logger

logger = get_logger(__name__)

def create_results_directories() -> List[str]:
    """
    Creates the results directory structure:
    - results/reports/
    - results/plots/

    Returns:
        List[str]: List of created directory paths.
    """
    results_root = get_results_dir()
    
    directories = [
        "reports",
        "plots"
    ]
    
    created_paths = []
    
    for subdir in directories:
        dir_path = results_root / subdir
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_paths.append(str(dir_path))
        else:
            logger.debug(f"Directory already exists: {dir_path}")
            
    return created_paths

def create_all_directories() -> List[str]:
    """
    Creates all project directory structures including code, data, tests, and results.
    This function orchestrates the creation of all required directories for the project.
    
    Returns:
        List[str]: List of all created directory paths.
    """
    from .config import get_project_root
    
    project_root = get_project_root()
    created_paths = []
    
    # Code directories
    code_dirs = [
        "code",
        "code/data",
        "code/models",
        "code/eval",
        "code/utils"
    ]
    
    # Data directories
    data_dirs = [
        "data",
        "data/raw",
        "data/processed",
        "data/splits",
        "data/schemas"
    ]
    
    # Tests directories
    tests_dirs = [
        "tests",
        "tests/contract",
        "tests/unit",
        "tests/integration"
    ]
    
    # Results directories
    results_dirs = [
        "results",
        "results/reports",
        "results/plots"
    ]
    
    all_dirs = code_dirs + data_dirs + tests_dirs + results_dirs
    
    for dir_path_str in all_dirs:
        dir_path = project_root / dir_path_str
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_paths.append(str(dir_path))
        else:
            logger.debug(f"Directory already exists: {dir_path}")
            
    return created_paths

def main():
    """
    Main entry point for directory creation.
    Creates the results directory structure and logs the outcome.
    """
    logger.info("Starting results directory creation...")
    created = create_results_directories()
    logger.info(f"Successfully created {len(created)} directories.")
    for path in created:
        logger.info(f"  - {path}")

if __name__ == "__main__":
    main()