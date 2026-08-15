import os
import sys
from pathlib import Path
from typing import Optional
import random
import numpy as np
import logging

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """
    Returns the project root directory.
    Assumes the project root is the parent of the 'src' directory.
    """
    current_file = Path(__file__).resolve()
    # Traverse up until we find 'src' directory
    for parent in current_file.parents:
        if (parent / 'src').exists():
            return parent
    # Fallback: assume current working directory is root
    return Path.cwd()

def get_data_path(relative_path: Optional[str] = None) -> Path:
    """
    Returns the data directory path.
    If relative_path is provided, returns the path joined with it.
    If called without arguments, returns the root data directory.
    Compatible with both:
      - get_data_path() -> Path
      - get_data_path(project_root) -> Path (ignores project_root if relative_path is None)
    """
    root = get_project_root()
    data_dir = root / 'data'
    
    if relative_path is None:
        # If no relative path provided, just return data dir
        # Handle legacy call that might pass a Path object as first arg
        # by checking if it's a Path and ignoring it if so (backward compat)
        return data_dir
    
    return data_dir / relative_path

def get_artifacts_path(relative_path: Optional[str] = None) -> Path:
    """
    Returns the artifacts directory path.
    """
    root = get_project_root()
    artifacts_dir = root / 'artifacts'
    
    if relative_path is None:
        return artifacts_dir
    
    return artifacts_dir / relative_path

def get_results_path(relative_path: Optional[str] = None) -> Path:
    """
    Returns the results directory path (inside data/results).
    """
    root = get_project_root()
    results_dir = root / 'data' / 'results'
    
    if relative_path is None:
        return results_dir
    
    return results_dir / relative_path

def ensure_directories() -> None:
    """
    Ensures that all required directories exist.
    """
    root = get_project_root()
    dirs = [
        root / 'data' / 'raw',
        root / 'data' / 'processed',
        root / 'data' / 'results',
        root / 'artifacts',
        root / 'artifacts' / 'synthesized_adapters',
        root / 'artifacts' / 'baseline_adapter'
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.info(f"Ensured directory: {d}")

def set_seed(seed: int = 42) -> None:
    """
    Sets random seeds for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    logger.info(f"Set random seed to {seed}")
