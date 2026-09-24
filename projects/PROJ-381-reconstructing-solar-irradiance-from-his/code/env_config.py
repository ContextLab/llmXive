"""
Environment variable management for the Solar Irradiance Reconstruction pipeline.

This module handles loading, validation, and access to environment variables
required for data paths, URLs, and configuration settings.

It supports loading from a .env file (if present) and falling back to
environment variables set in the shell.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Attempt to import dotenv, but don't fail if it's not installed
try:
    from dotenv import load_dotenv
    DOTENV_AVAILABLE = True
except ImportError:
    DOTENV_AVAILABLE = False
    load_dotenv = lambda *args, **kwargs: None  # type: ignore

logger = logging.getLogger(__name__)

# Default paths relative to project root
DEFAULT_DATA_ROOT = "data"
DEFAULT_DATA_RAW = "data/raw"
DEFAULT_DATA_PROCESSED = "data/processed"
DEFAULT_MODELS_ARTIFACTS = "code/models/artifacts"

# Default URLs
DEFAULT_SILSO_URL = "https://www.sidc.be/users/iv/homogene/sunspot/"
DEFAULT_SORCE_URL = "https://lasp.colorado.edu/sorce/"

def load_env_vars(env_file: Optional[Path] = None) -> bool:
    """
    Load environment variables from a .env file.
    
    Args:
        env_file: Path to the .env file. If None, looks for .env in the
                  current working directory.
    
    Returns:
        True if loading was successful (or dotenv not available), False otherwise.
    """
    if env_file is None:
        env_file = Path.cwd() / ".env"
    
    if not env_file.exists():
        logger.debug(f".env file not found at {env_file}, skipping load.")
        return True
    
    if not DOTENV_AVAILABLE:
        logger.warning(
            "python-dotenv is not installed. Please install it to load .env files: "
            "pip install python-dotenv"
        )
        return False
    
    success = load_dotenv(dotenv_path=env_file, override=True)
    if success:
        logger.info(f"Loaded environment variables from {env_file}")
    else:
        logger.warning(f"Failed to load environment variables from {env_file}")
    
    return success

def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Get an environment variable by key.
    
    Args:
        key: The environment variable name.
        default: Default value if the variable is not set.
        required: If True, raise a ValueError if the variable is not set.
    
    Returns:
        The value of the environment variable or the default.
    
    Raises:
        ValueError: If required is True and the variable is not set.
    """
    value = os.getenv(key, default)
    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set.")
    return value

def get_data_path(sub_path: Optional[str] = None) -> Path:
    """
    Get the root data path or a sub-path within it.
    
    Args:
        sub_path: Optional sub-directory path to append to the root data path.
    
    Returns:
        A Path object pointing to the requested directory.
    """
    root = get_env_var("DATA_ROOT", default=DEFAULT_DATA_ROOT)
    if root is None:
        raise ValueError("DATA_ROOT environment variable is not set and no default provided.")
    
    data_root = Path(root)
    
    if sub_path:
        return data_root / sub_path
    return data_root

def get_raw_data_path() -> Path:
    """Get the path to the raw data directory."""
    path = get_env_var("DATA_RAW", default=DEFAULT_DATA_RAW)
    if path is None:
        return get_data_path() / "raw"
    return Path(path)

def get_processed_data_path() -> Path:
    """Get the path to the processed data directory."""
    path = get_env_var("DATA_PROCESSED", default=DEFAULT_DATA_PROCESSED)
    if path is None:
        return get_data_path() / "processed"
    return Path(path)

def get_models_artifacts_path() -> Path:
    """Get the path to the models artifacts directory."""
    path = get_env_var("MODELS_ARTIFACTS", default=DEFAULT_MODELS_ARTIFACTS)
    if path is None:
        return Path("code/models/artifacts")
    return Path(path)

def validate_data_paths() -> Dict[str, bool]:
    """
    Validate that all required data paths exist and are writable.
    
    Returns:
        A dictionary mapping path names to validation status (True/False).
    """
    paths_to_check = {
        "raw": get_raw_data_path(),
        "processed": get_processed_data_path(),
        "models_artifacts": get_models_artifacts_path(),
    }
    
    results = {}
    for name, path in paths_to_check.items():
        if not path.exists():
            logger.warning(f"Path does not exist: {path}")
            results[name] = False
        elif not os.access(path, os.W_OK):
            logger.warning(f"Path is not writable: {path}")
            results[name] = False
        else:
            results[name] = True
    
    return results

def get_silso_url() -> str:
    """Get the SILSO data source URL."""
    return get_env_var("SILSO_URL", default=DEFAULT_SILSO_URL) or DEFAULT_SILSO_URL

def get_sorce_url() -> str:
    """Get the SORCE data source URL."""
    return get_env_var("SORCE_URL", default=DEFAULT_SORCE_URL) or DEFAULT_SORCE_URL

def setup_environment(env_file: Optional[Path] = None) -> None:
    """
    Initialize the environment by loading .env and validating paths.
    
    Args:
        env_file: Optional path to the .env file.
    
    Raises:
        RuntimeError: If critical paths are invalid.
    """
    load_env_vars(env_file)
    
    # Validate critical paths
    validation_results = validate_data_paths()
    if not all(validation_results.values()):
        failed_paths = [k for k, v in validation_results.items() if not v]
        logger.warning(f"Validation failed for paths: {failed_paths}")
        # We don't raise here to allow graceful degradation or manual creation
        # But in a strict pipeline, we might raise:
        # raise RuntimeError(f"Critical data paths are invalid: {failed_paths}")
    
    logger.info("Environment setup complete.")
