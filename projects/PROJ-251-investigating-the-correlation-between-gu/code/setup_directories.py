import os
import sys
from pathlib import Path
import logging
from utils.logging_config import get_logger

def create_directories(base_path: Path) -> None:
    """
    Create the required project directory structure.
    
    Directories created:
    - code/
    - data/raw
    - data/processed
    - data/results
    - data/research
    - tests/
    """
    logger = get_logger(__name__)
    
    directories = [
        base_path / "code",
        base_path / "data" / "raw",
        base_path / "data" / "processed",
        base_path / "data" / "results",
        base_path / "data" / "research",
        base_path / "tests",
    ]
    
    created_count = 0
    for directory in directories:
        if not directory.exists():
            directory.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {directory}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {directory}")
    
    logger.info(f"Directory setup complete. Created {created_count} new directories.")

def main() -> int:
    """
    Main entry point for directory setup.
    
    Returns:
        int: Exit code (0 for success, 1 for failure)
    """
    logger = get_logger(__name__)
    logger.info("Starting directory setup...")
    
    try:
        base_path = Path(__file__).resolve().parent.parent
        create_directories(base_path)
        logger.info("Directory setup completed successfully.")
        return 0
    except Exception as e:
        logger.error(f"Directory setup failed: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
