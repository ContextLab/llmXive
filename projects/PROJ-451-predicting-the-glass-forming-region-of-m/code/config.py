"""
Environment configuration management for API keys and dataset paths.

This module handles:
- Loading API keys (Materials Project) from environment variables
- Defining and validating data directory paths
- Ensuring required directories exist
"""
import os
import logging
from pathlib import Path
from typing import Optional

# Project root is assumed to be the parent of the 'code' directory
# If running as a script, we try to infer it, otherwise default to standard layout.
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default relative paths
_DATA_DIR = "data"
_RAW_DIR = "raw"
_PROCESSED_DIR = "processed"
_RESULTS_DIR = "results"

# Environment variable names
_ENV_MP_API_KEY = "MATERIALS_PROJECT_API_KEY"
_ENV_DATA_ROOT = "PROJECT_DATA_ROOT"

logger = logging.getLogger(__name__)


def get_materials_project_api_key() -> str:
    """
    Retrieve the Materials Project API key from the environment.

    Raises:
        RuntimeError: If the API key is not set.
    """
    api_key = os.getenv(_ENV_MP_API_KEY)
    if not api_key:
        raise RuntimeError(
            f"Environment variable {_ENV_MP_API_KEY} is not set. "
            "Please set it to your Materials Project API key."
        )
    return api_key


def get_materials_project_base_url() -> str:
    """
    Retrieve the base URL for the Materials Project API.
    Defaults to the production v3 endpoint.
    """
    return os.getenv("MATERIALS_PROJECT_BASE_URL", "https://api.materialsproject.org")


def _get_data_root() -> Path:
    """
    Determine the root directory for data artifacts.

    Priority:
    1. Environment variable PROJECT_DATA_ROOT
    2. Default: <project_root>/data
    """
    env_root = os.getenv(_ENV_DATA_ROOT)
    if env_root:
        return Path(env_root).resolve()
    return (_PROJECT_ROOT / _DATA_DIR).resolve()


def get_data_path() -> Path:
    """Returns the base data directory path."""
    return _get_data_root()


def get_raw_data_path() -> Path:
    """Returns the path to the raw data directory."""
    return get_data_path() / _RAW_DIR


def get_processed_data_path() -> Path:
    """Returns the path to the processed data directory."""
    return get_data_path() / _PROCESSED_DIR


def get_results_path() -> Path:
    """Returns the path to the results directory (for models, plots, etc.)."""
    return get_data_path() / _RESULTS_DIR


def get_custom_dataset_path(filename: str) -> Path:
    """
    Returns the full path for a custom dataset file within the processed directory.

    Args:
        filename: The name of the dataset file (e.g., 'my_dataset.csv').
    """
    return get_processed_data_path() / filename


def ensure_data_directories() -> None:
    """
    Creates all required data directories if they do not exist.

    Directories created:
    - data/raw
    - data/processed
    - data/results
    """
    dirs = [
        get_raw_data_path(),
        get_processed_data_path(),
        get_results_path(),
    ]

    for dir_path in dirs:
        if not dir_path.exists():
            logger.info(f"Creating directory: {dir_path}")
            dir_path.mkdir(parents=True, exist_ok=True)
        else:
            logger.debug(f"Directory already exists: {dir_path}")


def validate_environment() -> bool:
    """
    Validates that the environment is correctly configured.

    Checks:
    - Materials Project API key is set.
    - Data directories are writable.

    Returns:
        True if valid, raises RuntimeError otherwise.
    """
    # Check API Key
    try:
        get_materials_project_api_key()
    except RuntimeError as e:
        logger.error(f"API Key validation failed: {e}")
        raise

    # Check directories
    try:
        ensure_data_directories()
        # Try writing a temp file to ensure permissions
        for dir_path in [get_raw_data_path(), get_processed_data_path(), get_results_path()]:
            test_file = dir_path / ".write_test"
            test_file.touch()
            test_file.unlink()
    except OSError as e:
        logger.error(f"Directory validation failed: {e}")
        raise RuntimeError(f"Cannot write to data directories: {e}")

    logger.info("Environment validation successful.")
    return True


def init_environment() -> None:
    """
    Initializes the environment for the application.

    Performs:
    - Sets up logging (if not already configured).
    - Validates environment variables.
    - Ensures data directories exist.
    """
    if not logging.getLogger().handlers:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

    logger.info("Initializing environment...")
    validate_environment()
    ensure_data_directories()
    logger.info("Environment initialization complete.")
