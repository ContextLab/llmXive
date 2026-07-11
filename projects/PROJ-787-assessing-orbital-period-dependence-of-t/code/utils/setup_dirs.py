import os
import sys
from pathlib import Path
import logging
from utils.logging_config import get_logger

def initialize_directories(base_path: Path, dir_structure: list) -> bool:
    """
    Initialize a list of directories relative to base_path.
    
    Args:
        base_path: The root path where directories should be created.
        dir_structure: List of relative directory paths to create.
        
    Returns:
        True if all directories were created successfully, False otherwise.
    """
    logger = get_logger("utils.setup_dirs")
    all_success = True

    for rel_dir in dir_structure:
        target_path = base_path / rel_dir
        try:
            if not target_path.exists():
                target_path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {target_path}")
            else:
                logger.debug(f"Directory already exists: {target_path}")
            
            # Basic verification
            if not target_path.is_dir():
                logger.error(f"Path exists but is not a directory: {target_path}")
                all_success = False
        except PermissionError:
            logger.error(f"Permission denied creating directory: {target_path}")
            all_success = False
        except Exception as e:
            logger.error(f"Error creating directory {target_path}: {e}")
            all_success = False
    
    return all_success
