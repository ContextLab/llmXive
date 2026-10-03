"""
Scaffold module for initializing project directory structure.
Implements T001a: Initialize Project Directories.
"""
import os
import sys
import logging
from pathlib import Path
from typing import List, Tuple

# Import logger utility if available, otherwise use standard logging
try:
    from utils.logging_config import get_logger
    logger = get_logger(__name__)
except ImportError:
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

# Define the required directory structure relative to project root
REQUIRED_DIRS = [
    "data/raw",
    "data/processed",
    "data/outputs",
    "code/ingestion",
    "code/features",
    "code/models",
    "code/evaluation",
    "code/visualization",
    "code/utils",
    "tests/contract",
    "tests/integration",
]

def setup_directories(base_path: Path) -> Tuple[int, List[str]]:
    """
    Create all required directories and verify their existence.
    
    Args:
        base_path: The project root directory (Path).
        
    Returns:
        Tuple of (success_count, list of failed_paths)
    """
    created_count = 0
    failed_paths = []

    logger.info(f"Initializing directories relative to: {base_path}")

    for dir_name in REQUIRED_DIRS:
        full_path = base_path / dir_name
        try:
            if not full_path.exists():
                full_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {full_path}")
            
            # Verification step: test -d equivalent
            if full_path.is_dir():
                created_count += 1
            else:
                failed_paths.append(str(full_path))
                logger.error(f"Verification failed: {full_path} is not a directory.")
        except Exception as e:
            failed_paths.append(str(full_path))
            logger.error(f"Failed to create or verify {full_path}: {e}")

    return created_count, failed_paths

def main():
    """Entry point for directory initialization."""
    # Determine project root (assumed to be where this script is called from or parent of code/)
    # We look for the 'data' or 'specs' directory to find the root
    current = Path(__file__).resolve()
    # Walk up until we find a directory that looks like the project root
    # Typically 'code/ingestion' is deep, so we go up 2 levels to 'code', then 1 to root
    project_root = current.parent.parent 
    
    logger.info(f"Targeting project root: {project_root}")
    
    success_count, failures = setup_directories(project_root)
    
    total_required = len(REQUIRED_DIRS)
    if success_count == total_required:
        logger.info(f"SUCCESS: All {total_required} directories created and verified.")
        return 0
    else:
        logger.error(f"FAILURE: Only {success_count}/{total_required} directories created. "
                     f"Failed: {failures}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
