import os
from pathlib import Path
from typing import List
from utils.logging import get_logger

logger = get_logger(__name__)

def ensure_dirs(dir_paths: List[str]) -> None:
    """
    Create directories if they do not exist.
    
    Args:
        dir_paths: List of directory paths to create.
    """
    for path_str in dir_paths:
        path = Path(path_str)
        if not path.exists():
            path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {path}")
        else:
            logger.debug(f"Directory already exists: {path}")
