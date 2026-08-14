import os
import sys
from pathlib import Path
from typing import List
from utils.logging import get_logger, info, error

def setup_data_directories() -> List[str]:
    """
    Initialize the project directory structure.
    
    Creates the following directories relative to the project root:
    - code/
    - data/raw/
    - data/processed/
    - data/artifacts/
    - tests/
    - state/
    - figures/
    - analysis/
    - models/
    - training/
    
    Returns:
        List[str]: List of created directory paths (absolute).
    """
    # Determine project root (parent of code/)
    current_file = Path(__file__).resolve()
    code_root = current_file.parent
    project_root = code_root.parent
    
    # Define relative paths to create
    relative_paths = [
        "code",
        "code/data",
        "code/models",
        "code/training",
        "code/analysis",
        "code/utils",
        "code/tests",
        "data/raw",
        "data/processed",
        "data/artifacts",
        "figures",
        "state",
    ]
    
    created_dirs = []
    logger = get_logger(__name__)
    
    for rel_path in relative_paths:
        full_path = project_root / rel_path
        
        if not full_path.exists():
            try:
                full_path.mkdir(parents=True, exist_ok=True)
                created_dirs.append(str(full_path))
                info(f"Created directory: {full_path}")
            except OSError as e:
                error(f"Failed to create directory {full_path}: {e}")
                raise
        else:
            info(f"Directory already exists: {full_path}")
    
    if created_dirs:
        info(f"Successfully created {len(created_dirs)} directories.")
    else:
        info("No new directories created (all exist).")
        
    return created_dirs
