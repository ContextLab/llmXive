"""
Environment Variable Management for Solar Irradiance Reconstruction Project.

This module handles loading, validating, and providing access to environment
variables and configuration paths defined in the .env file.
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Attempt to import dotenv; if missing, provide a graceful degradation or error
try:
    from dotenv import load_dotenv
except ImportError:
        raise ImportError(
            "python-dotenv is required for environment management. "
            "Install it via: pip install python-dotenv"
        )

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global cache for loaded environment variables to avoid re-parsing
_ENV_VARS: Dict[str, str] = {}
_IS_LOADED = False

def load_env_vars(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file.

    Args:
        env_path: Path to the .env file. Defaults to PROJECT_ROOT/.env.

    Returns:
        Dictionary of loaded environment variables.
    """
    global _ENV_VARS, _IS_LOADED

    if _IS_LOADED:
        return _ENV_VARS

    if env_path is None:
        # Default to project root .env
        project_root = Path(__file__).resolve().parent.parent
        env_path = project_root / ".env"

    if not env_path.exists():
        # Check for .env.example as a fallback for guidance, but don't load it as config
        example_path = env_path.with_name(".env.example")
        if example_path.exists():
            logger.warning(f"Configuration file {env_path} not found. "
                           f"Please copy .env.example to .env and configure paths.")
            # Load from example just to provide defaults if needed, but warn
            # For strictness, we might prefer to fail if .env is missing.
            # However, for this task, we load defaults if .env is missing but .env.example exists?
            # No, standard practice: if .env missing, use system env or fail.
            # Let's try to load from .env if it exists, otherwise use os.environ defaults.
            pass
        else:
            logger.warning("No .env file found. Using system environment variables.")

    # Load using python-dotenv
    if env_path.exists():
        load_dotenv(dotenv_path=env_path, override=True)
        logger.info(f"Loaded environment variables from {env_path}")
    else:
        logger.info("No .env file found. Relying on system environment variables.")

    # Capture current state of os.environ into our cache
    _ENV_VARS = dict(os.environ)
    _IS_LOADED = True

    return _ENV_VARS

def get_env_var(key: str, default: Optional[str] = None, required: bool = False) -> Optional[str]:
    """
    Retrieve an environment variable.

    Args:
        key: The environment variable name.
        default: Default value if the variable is not set.
        required: If True, raises ValueError if the variable is missing.

    Returns:
        The value of the environment variable or default.

    Raises:
        ValueError: If required is True and the variable is not set.
    """
    if not _IS_LOADED:
        load_env_vars()

    value = os.environ.get(key, default)

    if required and value is None:
        raise ValueError(f"Required environment variable '{key}' is not set.")

    return value

def get_data_path(sub_dir: Optional[str] = None) -> Path:
    """
    Get the absolute path to the data directory.

    Args:
        sub_dir: Optional subdirectory relative to the data root.

    Returns:
        Path object for the data directory.
    """
    data_root = get_env_var("DATA_ROOT", default="data")
    base_path = Path(data_root).resolve()

    if sub_dir:
        return base_path / sub_dir
    return base_path

def validate_data_paths() -> bool:
    """
    Validate that all configured data paths exist and are writable.

    Returns:
        True if all paths are valid, False otherwise.
    """
    if not _IS_LOADED:
        load_env_vars()

    validate_flag = get_env_var("VALIDATE_PATHS", default="false").lower() == "true"

    if not validate_flag:
        logger.info("Path validation skipped (VALIDATE_PATHS=false).")
        return True

    paths_to_check = [
        ("DATA_RAW_DIR", "data/raw"),
        ("DATA_PROCESSED_DIR", "data/processed"),
        ("MODEL_ARTIFACTS_DIR", "code/models/artifacts"),
    ]

    all_valid = True
    for env_key, default_path in paths_to_check:
        path_str = get_env_var(env_key, default=default_path)
        if not path_str:
            logger.error(f"Path variable {env_key} is not set.")
            all_valid = False
            continue

        path = Path(path_str).resolve()

        if not path.exists():
            logger.warning(f"Path does not exist: {path}. Attempting to create...")
            try:
                path.mkdir(parents=True, exist_ok=True)
                logger.info(f"Created directory: {path}")
            except OSError as e:
                logger.error(f"Failed to create directory {path}: {e}")
                all_valid = False
        elif not path.is_dir():
            logger.error(f"Path exists but is not a directory: {path}")
            all_valid = False
        else:
            # Check write permission
            try:
                test_file = path / ".write_test"
                test_file.touch()
                test_file.unlink()
            except OSError as e:
                logger.error(f"Directory {path} is not writable: {e}")
                all_valid = False

    return all_valid

def get_silso_url() -> str:
    """Get the SILSO data URL."""
    return get_env_var("SILSO_URL", required=True)

def get_sorce_url() -> str:
    """Get the SORCE data URL."""
    return get_env_var("SORCE_URL", required=True)

def get_model_artifacts_path() -> Path:
    """Get the model artifacts directory path."""
    path_str = get_env_var("MODEL_ARTIFACTS_DIR", default="code/models/artifacts")
    return Path(path_str).resolve()

def setup_environment() -> None:
    """
    Main entry point to setup and validate the environment.
    This should be called at the start of any script.
    """
    logger.info("Setting up environment...")
    load_env_vars()
    
    # Set logging level from env
    log_level = get_env_var("LOG_LEVEL", default="INFO").upper()
    logger.setLevel(log_level)
    logging.getLogger().setLevel(log_level)

    # Validate paths if configured
    if not validate_data_paths():
        logger.error("Environment setup failed due to invalid paths.")
        raise RuntimeError("Environment validation failed.")
    
    logger.info("Environment setup complete.")

# For command-line testing
if __name__ == "__main__":
    setup_environment()
    print("Environment variables loaded successfully.")
    print(f"Data Root: {get_data_path()}")
    print(f"SILSO URL: {get_silso_url()}")
    print(f"SORCE URL: {get_sorce_url()}")
