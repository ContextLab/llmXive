"""
Configuration management for the Glass Forming Region prediction pipeline.

Handles environment variable loading, validation, and global constants.
"""
import os
import logging
from pathlib import Path
from typing import Optional

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global constants per task specification
LABEL_DROP_THRESHOLD = 0.05
CV_STABILITY_THRESHOLD = 0.05
MIN_DATASET_SIZE = 1000

class ConfigValidationError(Exception):
    """Raised when configuration validation fails."""
    pass

def get_env_path() -> Path:
    """Return the path to the .env file."""
    # Assume .env is in the project root (code/../.env) or code/.env
    project_root = Path(__file__).resolve().parent.parent
    env_path = project_root / ".env"
    if not env_path.exists():
        # Fallback to code/.env if project root one doesn't exist
        env_path = Path(__file__).parent.parent / ".env" 
        if not env_path.exists():
            # Check relative to current working directory
            env_path = Path.cwd() / ".env"
    return env_path

def load_env_vars(env_path: Optional[Path] = None) -> dict:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. Defaults to auto-detection.
        
    Returns:
        Dictionary of environment variables.
    """
    if env_path is None:
        env_path = get_env_path()
    
    env_vars = {}
    if env_path.exists():
        logger.info(f"Loading environment from {env_path}")
        with open(env_path, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith("#"):
                    if "=" in line:
                        key, value = line.split("=", 1)
                        env_vars[key.strip()] = value.strip()
    else:
        logger.warning(f".env file not found at {env_path}")
        
    return env_vars

def _get_config_value(key: str, required: bool = False, env_vars: Optional[dict] = None) -> Optional[str]:
    """
    Helper to get a config value from environment or .env file.
    
    Args:
        key: The environment variable name.
        required: If True, raise ConfigValidationError if missing/empty.
        env_vars: Pre-loaded env vars (optional optimization).
        
    Returns:
        The value or None if not found and not required.
    """
    if env_vars is None:
        env_vars = load_env_vars()
        
    # Check os.environ first (system env vars override .env)
    value = os.environ.get(key)
    if value is None:
        value = env_vars.get(key)
        
    if required:
        if value is None or value.strip() == "":
            raise ConfigValidationError(
                f"Required configuration '{key}' is missing or empty. "
                f"Please set it in your .env file or environment variables."
            )
    return value

def get_materials_project_api_key(env_vars: Optional[dict] = None) -> str:
    """Get the Materials Project API key."""
    return _get_config_value("MATERIALS_PROJECT_API_KEY", required=True, env_vars=env_vars)

def get_materials_project_base_url(env_vars: Optional[dict] = None) -> str:
    """Get the Materials Project API base URL (default provided)."""
    return _get_config_value("MATERIALS_PROJECT_BASE_URL", required=False, env_vars=env_vars) or "https://next-gen.materialsproject.org/api"

def get_zenodo_doi(env_vars: Optional[dict] = None) -> str:
    """Get the Zenodo DOI/Record ID."""
    return _get_config_value("ZENO_DO_ID", required=True, env_vars=env_vars)

def get_data_path(env_vars: Optional[dict] = None) -> Path:
    """Get the base data directory path."""
    project_root = Path(__file__).resolve().parent.parent
    return project_root / "data"

def get_raw_data_path(env_vars: Optional[dict] = None) -> Path:
    """Get the raw data directory path."""
    return get_data_path(env_vars) / "raw"

def get_processed_data_path(env_vars: Optional[dict] = None) -> Path:
    """Get the processed data directory path."""
    return get_data_path(env_vars) / "processed"

def get_results_path(env_vars: Optional[dict] = None) -> Path:
    """Get the results directory path."""
    project_root = Path(__file__).resolve().parent.parent
    return project_root / "data" / "results"

def get_custom_dataset_path(env_vars: Optional[dict] = None) -> Path:
    """Get the custom dataset directory path."""
    return get_data_path(env_vars) / "custom"

def ensure_data_directories(env_vars: Optional[dict] = None) -> None:
    """Ensure all required data directories exist."""
    dirs = [
        get_raw_data_path(env_vars),
        get_processed_data_path(env_vars),
        get_results_path(env_vars),
        get_custom_dataset_path(env_vars)
    ]
    for d in dirs:
        d.mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {d}")

def validate_environment(env_vars: Optional[dict] = None) -> None:
    """
    Validate that all required environment variables are set.
    
    Raises:
        ConfigValidationError: If any required variable is missing or empty.
    """
    # This function primarily validates required keys
    # It will raise ConfigValidationError if they are missing
    try:
        get_materials_project_api_key(env_vars)
        get_zenodo_doi(env_vars)
        logger.info("Environment validation passed.")
    except ConfigValidationError as e:
        logger.error(f"Configuration validation failed: {e}")
        raise

def init_environment(env_vars: Optional[dict] = None) -> dict:
    """
    Initialize the environment: validate and ensure directories.
    
    Returns:
        Dictionary of loaded environment variables.
    """
    if env_vars is None:
        env_vars = load_env_vars()
        
    validate_environment(env_vars)
    ensure_data_directories(env_vars)
    return env_vars

# Export constants for direct import
__all__ = [
    "ConfigValidationError",
    "LABEL_DROP_THRESHOLD",
    "CV_STABILITY_THRESHOLD",
    "MIN_DATASET_SIZE",
    "get_env_path",
    "load_env_vars",
    "get_materials_project_api_key",
    "get_materials_project_base_url",
    "get_zenodo_doi",
    "get_data_path",
    "get_raw_data_path",
    "get_processed_data_path",
    "get_results_path",
    "get_custom_dataset_path",
    "ensure_data_directories",
    "validate_environment",
    "init_environment"
]