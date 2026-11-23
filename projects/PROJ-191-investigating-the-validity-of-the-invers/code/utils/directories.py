import os
import sys
import logging
from pathlib import Path
from typing import List
from config import get_logger, setup_logging

def ensure_data_directories(base_path: Path, logger: logging.Logger) -> None:
    """
    Ensure the required data directory structure exists using robust mkdir -p logic.
    
    Creates the following directories relative to base_path:
    - data/raw/
    - data/processed/
    - data/results/
    
    Args:
        base_path: The root project directory (e.g., projects/PROJ-191-...)
        logger: Logger instance for status messages
    """
    relative_dirs = [
        "data/raw",
        "data/processed",
        "data/results"
    ]
    
    created_count = 0
    for rel_dir in relative_dirs:
        target_path = base_path / rel_dir
        
        if not target_path.exists():
            try:
                target_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {target_path}")
                created_count += 1
            except OSError as e:
                logger.error(f"Failed to create directory {target_path}: {e}")
                raise
        else:
            if not target_path.is_dir():
                logger.error(f"Path exists but is not a directory: {target_path}")
                raise NotADirectoryError(f"Path exists but is not a directory: {target_path}")
            else:
                logger.debug(f"Directory already exists: {target_path}")
    
    if created_count > 0:
        logger.info(f"Successfully created {created_count} new directory(ies).")
    else:
        logger.info("All required directories already existed.")

def main() -> None:
    """
    CLI entry point to ensure data directories exist.
    
    Expects the current working directory to be the project root or
    accepts an optional --base-path argument.
    """
    setup_logging()
    logger = get_logger("setup_dirs")
    
    # Determine base path: prefer command line arg, else cwd
    base_path = Path.cwd()
    if len(sys.argv) > 1:
        base_path = Path(sys.argv[1])
    
    if not base_path.is_absolute():
        base_path = Path.cwd() / base_path
    
    logger.info(f"Ensuring data directories under: {base_path}")
    
    if not base_path.exists():
        logger.error(f"Base path does not exist: {base_path}")
        sys.exit(1)
    
    ensure_data_directories(base_path, logger)
    logger.info("Directory structure verification complete.")

if __name__ == "__main__":
    main()