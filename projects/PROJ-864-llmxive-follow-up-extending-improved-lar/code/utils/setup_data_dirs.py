import os
import sys
from pathlib import Path
from typing import List

from utils.logging import get_logger, info, error

logger = get_logger(__name__)

def setup_data_directories() -> List[str]:
    """
    Create the required data directory structure for the project.
    
    Creates:
    - data/raw/
    - data/processed/
    - data/artifacts/
    
    Returns a list of created directory paths.
    
    Raises:
        OSError: If a directory cannot be created.
        PermissionError: If the process lacks write permissions.
    """
    # Determine the project root relative to this module
    # Assuming this file is at code/utils/setup_data_dirs.py
    # Project root is 3 levels up: code/utils -> code -> root
    current_file = Path(__file__).resolve()
    code_root = current_file.parent
    project_root = code_root.parent
    data_root = project_root / "data"
    
    directories = [
        "raw",
        "processed",
        "artifacts"
    ]
    
    created_paths = []
    
    for dir_name in directories:
        dir_path = data_root / dir_name
        
        if not dir_path.exists():
            try:
                dir_path.mkdir(parents=True, exist_ok=True)
                created_paths.append(str(dir_path))
                info(f"Created directory: {dir_path}")
            except PermissionError as e:
                error(f"Permission denied creating directory {dir_path}: {e}")
                raise
            except OSError as e:
                error(f"Error creating directory {dir_path}: {e}")
                raise
        else:
            info(f"Directory already exists: {dir_path}")
            created_paths.append(str(dir_path))
    
    if not created_paths:
        info("All required data directories already exist.")
    else:
        info(f"Successfully created {len(created_paths)} data directories.")
        
    return created_paths
