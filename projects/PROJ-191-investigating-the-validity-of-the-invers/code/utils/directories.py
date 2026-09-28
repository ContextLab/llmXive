import os
import sys
import logging
from pathlib import Path
from typing import List
from config import get_logger, setup_logging

def ensure_data_directories(base_path: Path, dirs: List[str]) -> None:
    """
    Ensure the specified directory structure exists under base_path.
    Uses robust mkdir -p logic (creates parents if missing, ignores if exists).
    
    Args:
        base_path: The root directory to create subdirectories under.
        dirs: List of relative directory paths to ensure exist.
    """
    logger = get_logger(__name__)
    
    for d in dirs:
        target_path = base_path / d
        try:
            target_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Ensured directory: {target_path}")
        except PermissionError:
            logger.error(f"Permission denied creating directory: {target_path}")
            raise
        except OSError as e:
            logger.error(f"OS error creating directory {target_path}: {e}")
            raise

def main() -> None:
    """
    Entry point for T007: Ensure directory structure for data/raw/, 
    data/processed/, and data/results/ exists.
    
    This script is designed to be run as: python code/utils/directories.py
    """
    # Setup logging
    setup_logging()
    logger = get_logger(__name__)
    
    # Determine the project root. 
    # The script is at code/utils/directories.py, so project root is 3 levels up.
    script_path = Path(__file__).resolve()
    project_root = script_path.parent.parent.parent
    
    # Define the required directories relative to the project root
    required_dirs = [
        "data/raw",
        "data/processed",
        "data/results"
    ]
    
    logger.info(f"Project root detected at: {project_root}")
    logger.info(f"Ensuring directories exist under: {project_root}")
    
    ensure_data_directories(project_root, required_dirs)
    
    # Verify existence
    for d in required_dirs:
        target = project_root / d
        if not target.exists():
            logger.critical(f"Failed to create directory: {target}")
            sys.exit(1)
        if not target.is_dir():
            logger.critical(f"Path exists but is not a directory: {target}")
            sys.exit(1)
    
    logger.info("All required directories successfully created or verified.")
