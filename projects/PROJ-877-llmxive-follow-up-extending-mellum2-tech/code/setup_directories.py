"""
Project Directory Initialization Module.
Creates the standard project structure for llmXive research artifacts.
"""
import os
import logging
from pathlib import Path
from typing import List, Tuple

# Import local logger configuration to ensure consistent logging
try:
    from utils.logging import get_logger
    logger = get_logger("setup_directories")
except ImportError:
    # Fallback if utils.logging isn't fully initialized yet
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("setup_directories")

# Project Root Definition
# The task specifies the root is projects/PROJ-877-llmxive-follow-up-extending-mellum2-tech/
# This script assumes it is run from within that root directory.
PROJECT_ROOT = Path.cwd()

# Standard directories to ensure exist
STANDARD_DIRS = [
    "code",
    "data",
    "tests",
    "specs",
    "figures",
    "logs",
    "data/raw",
    "data/processed",
    "data/results",
    "tests/unit",
    "tests/integration",
    "code/utils",
    "code/data",
    "code/analysis",
    "code/inference",
    "code/contracts",
]

def ensure_data_directories() -> List[str]:
    """
    Creates the standard directory structure if it does not exist.
    Returns a list of created directory paths.
    """
    created_dirs = []
    
    for dir_name in STANDARD_DIRS:
        target_path = PROJECT_ROOT / dir_name
        if not target_path.exists():
            target_path.mkdir(parents=True, exist_ok=True)
            created_dirs.append(str(target_path))
            logger.info(f"Created directory: {target_path}")
        else:
            logger.debug(f"Directory already exists: {target_path}")
    
    return created_dirs

def generate_init_files() -> List[str]:
    """
    Creates __init__.py files in all Python package directories to make them importable.
    """
    init_files = []
    python_dirs = ["code", "code/utils", "code/data", "code/analysis", 
                   "code/inference", "code/contracts", "tests", "tests/unit", "tests/integration"]
    
    for dir_name in python_dirs:
        target_path = PROJECT_ROOT / dir_name / "__init__.py"
        if not target_path.exists():
            # Create an empty init file or a simple header
            target_path.write_text(f'"""Auto-generated init for {dir_name}."""\n')
            init_files.append(str(target_path))
            logger.info(f"Created init file: {target_path}")
    
    return init_files

def main():
    """
    Entry point for directory initialization.
    Creates structure and prints a summary log.
    """
    logger.info(f"Initializing project structure at: {PROJECT_ROOT}")
    
    created_dirs = ensure_data_directories()
    init_files = generate_init_files()
    
    total_created = len(created_dirs) + len(init_files)
    logger.info(f"Initialization complete. Created {total_created} items.")
    
    if not created_dirs and not init_files:
        logger.info("No new items created; structure already exists.")
    else:
        logger.info("Created directories:")
        for d in created_dirs:
            logger.info(f"  - {d}")
        logger.info("Created init files:")
        for f in init_files:
            logger.info(f"  - {f}")

if __name__ == "__main__":
    main()