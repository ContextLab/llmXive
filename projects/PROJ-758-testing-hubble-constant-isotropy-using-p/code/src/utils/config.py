"""
Configuration management for the Hubble Constant Isotropy project.

Handles environment variables for API keys (Zenodo), random seed management,
and project directory path resolution.
"""

import os
import random
from pathlib import Path
from typing import Optional

# Import logger from sibling module as per API surface
from .logger import get_logger

# Initialize logger for this module
logger = get_logger(__name__)

# Project root is assumed to be the parent of 'code/'
# If running from 'code/', parent is root. If running from root, 'code' is subdir.
# We assume the standard execution context where this file is in code/src/utils/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent.parent
_CONFIG_FILE_PATH = _PROJECT_ROOT / "config" / "settings.ini"

# Environment variable names
_ZENODO_API_KEY_ENV = "ZENODO_API_KEY"
_RANDOM_SEED_ENV = "RANDOM_SEED"

def get_zenodo_api_key(required: bool = True) -> Optional[str]:
    """
    Retrieve the Zenodo API key from environment variables.

    Args:
        required: If True, raises an error if the key is missing.
                 If False, returns None if missing.

    Returns:
        The API key string if found.

    Raises:
        ValueError: If the key is required but not found.
    """
    key = os.getenv(_ZENODO_API_KEY_ENV)
    if not key:
        if required:
            msg = (
                f"Zenodo API key not found in environment variable "
                f"'{_ZENODO_API_KEY_ENV}'. "
                f"Please set it to access the Pantheon+ dataset."
            )
            logger.error(msg)
            raise ValueError(msg)
        logger.warning(
            f"Zenodo API key not found in environment variable "
            f"'{_ZENODO_API_KEY_ENV}'. Some features may be unavailable."
        )
        return None
    
    logger.info("Zenodo API key loaded successfully.")
    return key

def set_random_seed(seed: Optional[int] = None) -> int:
    """
    Initialize the random seed for reproducibility.

    Checks for 'RANDOM_SEED' environment variable first. If not set,
    uses the provided argument, or defaults to 42 if neither is available.

    Args:
        seed: An integer seed value. If None, checks environment.

    Returns:
        The integer seed value used.
    """
    env_seed = os.getenv(_RANDOM_SEED_ENV)
    
    if env_seed is not None:
        try:
            final_seed = int(env_seed)
            logger.info(f"Random seed initialized from environment: {final_seed}")
        except ValueError:
            logger.warning(
                f"Invalid random seed in environment '{_RANDOM_SEED_ENV}': "
                f"'{env_seed}'. Using provided seed or default."
            )
            final_seed = seed if seed is not None else 42
    elif seed is not None:
        final_seed = seed
        logger.info(f"Random seed initialized from argument: {final_seed}")
    else:
        final_seed = 42
        logger.warning(
            f"No random seed specified. Using default: {final_seed}. "
            f"Set {_RANDOM_SEED_ENV} or pass seed argument for reproducibility."
        )

    # Set seeds for standard libraries used in this project
    random.seed(final_seed)
    
    # Note: numpy and torch seeds would be set here if those were imported,
    # but we stick to standard library + provided API surface.
    
    return final_seed

def get_project_paths() -> dict:
    """
    Returns a dictionary of key project directory paths.

    Returns:
        dict: Mapping of logical names to Path objects.
    """
    paths = {
        "root": _PROJECT_ROOT,
        "data_raw": _PROJECT_ROOT / "data" / "raw",
        "data_processed": _PROJECT_ROOT / "data" / "processed",
        "data_results": _PROJECT_ROOT / "data" / "results",
        "code": _PROJECT_ROOT / "code",
        "src": _PROJECT_ROOT / "code" / "src",
        "tests": _PROJECT_ROOT / "tests",
        "config": _PROJECT_ROOT / "config",
        "figures": _PROJECT_ROOT / "figures",
    }
    logger.debug(f"Project paths resolved: {list(paths.keys())}")
    return paths

def ensure_directories_exist() -> None:
    """
    Ensures all required project directories exist, creating them if necessary.
    
    Uses paths derived from get_project_paths().
    """
    paths = get_project_paths()
    dirs_to_create = [
        paths["data_raw"],
        paths["data_processed"],
        paths["data_results"],
        paths["config"],
        paths["figures"],
    ]

    created_count = 0
    for dir_path in dirs_to_create:
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            logger.info(f"Created directory: {dir_path}")
            created_count += 1
        else:
            logger.debug(f"Directory already exists: {dir_path}")
    
    if created_count > 0:
        logger.info(f"Created {created_count} new directories.")

def get_config_summary() -> dict:
    """
    Generates a summary of the current configuration state.
    
    Returns:
        dict: Summary including seed status, API key presence, and paths.
    """
    seed = os.getenv(_RANDOM_SEED_ENV, "Not set (default 42)")
    has_key = _ZENODO_API_KEY_ENV in os.environ
    paths = get_project_paths()
    
    summary = {
        "random_seed_env": seed,
        "zenodo_api_key_present": has_key,
        "project_root": str(paths["root"]),
        "data_dirs": {
            "raw": str(paths["data_raw"]),
            "processed": str(paths["data_processed"]),
            "results": str(paths["data_results"]),
        }
    }
    logger.debug(f"Configuration summary generated: {summary}")
    return summary