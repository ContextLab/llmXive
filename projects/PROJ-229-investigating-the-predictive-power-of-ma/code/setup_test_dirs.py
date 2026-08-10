import os
import logging
from pathlib import Path
from typing import List
from config import get_config
from code.utils.logger import get_pipeline_logger

def create_test_directories() -> List[Path]:
    """
    Creates the required test directories for the project.
    
    Returns:
        List[Path]: A list of paths to the created directories.
    """
    config = get_config()
    base_path = Path(config.get("project_root", "."))
    test_root = base_path / "tests"
    
    required_dirs = [
        test_root / "unit",
        test_root / "integration",
        test_root / "contract"
    ]
    
    created_dirs = []
    for dir_path in required_dirs:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logging.info(f"Created test directory: {dir_path}")
            created_dirs.append(dir_path)
        else:
            logging.debug(f"Test directory already exists: {dir_path}")
            created_dirs.append(dir_path)
        
        # Ensure __init__.py exists to make them packages
        init_file = dir_path / "__init__.py"
        if not init_file.exists():
            init_file.touch()
            logging.debug(f"Created __init__.py in {dir_path}")
    
    return created_dirs

def main():
    """
    Main entry point for creating test directories.
    """
    logger = get_pipeline_logger()
    logger.info("Starting test directory creation...")
    
    try:
        dirs = create_test_directories()
        logger.info(f"Successfully created/verified {len(dirs)} test directories.")
        for d in dirs:
            logger.info(f"  - {d}")
    except Exception as e:
        logger.error(f"Failed to create test directories: {e}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
