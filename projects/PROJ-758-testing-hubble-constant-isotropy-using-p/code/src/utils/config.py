"""
Environment variable management and configuration for the Hubble Constant Isotropy project.

This module handles:
- Zenodo API key retrieval
- Random seed management for reproducibility
- Environment variable validation
"""

import os
import random
from pathlib import Path
from typing import Optional

from .logger import get_logger

logger = get_logger(__name__)

# Default random seed for reproducibility if not specified
DEFAULT_SEED = 42

# Zenodo configuration
ZENODO_RECORD_ID = "1002345"
ZENODO_DOI = "10.5281/zenodo.1002345"
ZENODO_API_KEY_ENV = "ZENODO_API_KEY"
ZENODO_BASE_URL = "https://zenodo.org/api/records"

# Project paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
RESULTS_DIR = DATA_DIR / "results"

def get_zenodo_api_key() -> Optional[str]:
    """
    Retrieve the Zenodo API key from environment variables.

    Returns:
        The API key string if found, None otherwise.

    Raises:
        ValueError: If the API key is expected but not found (for critical operations).
    """
    api_key = os.getenv(ZENODO_API_KEY_ENV)
    if api_key:
        logger.info("Zenodo API key found in environment")
    else:
        logger.warning("Zenodo API key not found in environment. Some operations may be rate-limited.")
    return api_key

def set_random_seed(seed: Optional[int] = None) -> int:
    """
    Set the random seed for reproducible experiments.

    Args:
        seed: The seed value. If None, uses DEFAULT_SEED.

    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = DEFAULT_SEED

    # Set seeds for various libraries
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        logger.warning("NumPy not available, skipping numpy random seed")

    try:
        import os
        os.environ['PYTHONHASHSEED'] = str(seed)
    except Exception:
        logger.warning("Could not set PYTHONHASHSEED")

    logger.info(f"Random seed set to {seed}")
    return seed

def get_project_paths() -> dict:
    """
    Retrieve standardized project directory paths.

    Returns:
        Dictionary mapping path names to Path objects.
    """
    return {
        "root": PROJECT_ROOT,
        "data": DATA_DIR,
        "raw": RAW_DATA_DIR,
        "processed": PROCESSED_DATA_DIR,
        "results": RESULTS_DIR,
    }

def ensure_directories_exist() -> bool:
    """
    Ensure all required project directories exist.

    Returns:
        True if all directories exist or were created successfully.
    """
    paths = get_project_paths()
    success = True
    for name, path in paths.items():
        if not path.exists():
            try:
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {path}")
            except Exception as e:
                logger.error(f"Failed to create directory {path}: {e}")
                success = False
    return success

def get_config_summary() -> dict:
    """
    Get a summary of the current configuration state.

    Returns:
        Dictionary with configuration details.
    """
    return {
        "zenodo_record_id": ZENODO_RECORD_ID,
        "zenodo_doi": ZENODO_DOI,
        "api_key_present": get_zenodo_api_key() is not None,
        "project_root": str(PROJECT_ROOT),
        "data_dir": str(DATA_DIR),
        "default_seed": DEFAULT_SEED,
    }