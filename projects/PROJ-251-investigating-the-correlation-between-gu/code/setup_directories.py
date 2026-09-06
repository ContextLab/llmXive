import os
import sys
from pathlib import Path
import logging
from utils.logging_config import get_logger

def create_directories(base_path: Path) -> None:
    """
    Create the required project directory structure.
    
    Directories created relative to base_path:
    - code/
    - data/raw
    - data/processed
    - data/results
    - data/research
    - tests/
    """
    logger = get_logger(__name__)
    
    directories = [
        "code",
        "data/raw",
        "data/processed",
        "data/results",
        "data/research",
        "tests"
    ]
    
    for dir_name in directories:
        dir_path = base_path / dir_name
        try:
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
        except OSError as e:
            logger.error(f"Failed to create directory {dir_path}: {e}")
            raise

def main() -> int:
    """
    Main entry point for directory setup.
    
    Returns:
        int: 0 on success, 1 on failure
    """
    logger = get_logger(__name__)
    logger.info("Starting directory setup...")
    
    try:
        # Determine project root (assuming script is in code/ directory)
        script_path = Path(__file__).resolve()
        project_root = script_path.parent.parent
        
        create_directories(project_root)
        
        logger.info("Directory setup completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Directory setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
