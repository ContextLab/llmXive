"""
Environment variable management for the Solar Irradiance Reconstruction project.

This module handles loading, validating, and providing access to environment variables
that control data paths and configuration settings.

It supports:
1. Loading from a .env file in the project root
2. Fallback to os.environ
3. Default values derived from project structure
4. Validation of path existence
"""

import os
from pathlib import Path
from typing import Optional, Dict, Any
import logging

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Default relative paths from project root
DEFAULT_DATA_ROOT = "data"
DEFAULT_DATA_RAW = "data/raw"
DEFAULT_DATA_PROCESSED = "data/processed"
DEFAULT_MODEL_ARTIFACTS = "code/models/artifacts"
DEFAULT_DATA_FIGURES = "data/figures"

# Environment variable names
ENV_DATA_ROOT = "DATA_ROOT_PATH"
ENV_DATA_RAW = "DATA_RAW_PATH"
ENV_DATA_PROCESSED = "DATA_PROCESSED_PATH"
ENV_MODEL_ARTIFACTS = "MODEL_ARTIFACTS_PATH"
ENV_DATA_FIGURES = "DATA_FIGURES_PATH"
ENV_SILSO_URL = "SILSO_URL"
ENV_SORCE_URL = "SORCE_URL"

# Default URLs
DEFAULT_SILSO_URL = "https://www.sidc.be/users/silso/datafiles/monthlydata_files/"
DEFAULT_SORCE_URL = "https://lasp.colorado.edu/sorce/data/tim/"

# Project root (assumed to be the directory containing 'code/')
# In a real deployment, this might be passed explicitly or detected differently
_PROJECT_ROOT: Optional[Path] = None

def _get_project_root() -> Path:
    """Determine the project root directory."""
    global _PROJECT_ROOT
    if _PROJECT_ROOT is None:
        # Start from current working directory
        cwd = Path.cwd()
        # Look for the 'code' directory to identify project root
        if (cwd / "code").exists():
            _PROJECT_ROOT = cwd
        elif (cwd / "code" / "env_manager.py").exists():
            _PROJECT_ROOT = cwd
        else:
            # Fallback: assume current directory is root
            _PROJECT_ROOT = cwd
        logger.info(f"Detected project root at: {_PROJECT_ROOT}")
    return _PROJECT_ROOT

def load_env_vars(env_path: Optional[Path] = None) -> Dict[str, str]:
    """
    Load environment variables from a .env file.
    
    Args:
        env_path: Path to the .env file. If None, looks for .env in project root.
    
    Returns:
        Dictionary of loaded environment variables.
    """
    if env_path is None:
        project_root = _get_project_root()
        env_path = project_root / "code" / ".env"
        if not env_path.exists():
            # Try root directory
            env_path = project_root / ".env"
    
    env_vars = {}
    if env_path.exists():
        logger.info(f"Loading environment variables from {env_path}")
        with open(env_path, 'r') as f:
            for line in f:
                line = line.strip()
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    env_vars[key] = value
        logger.info(f"Loaded {len(env_vars)} environment variables")
    else:
        logger.warning(f".env file not found at {env_path}. Using os.environ and defaults.")
    
    return env_vars

def get_env_var(key: str, default: Optional[str] = None, env_vars: Optional[Dict[str, str]] = None) -> Optional[str]:
    """
    Get an environment variable with fallback chain:
    1. Passed env_vars dict (if provided)
    2. os.environ
    3. Default value (if provided)
    
    Args:
        key: The environment variable name.
        default: Default value if not found.
        env_vars: Optional dictionary of loaded env vars (from load_env_vars).
    
    Returns:
        The value of the environment variable or the default.
    """
    if env_vars and key in env_vars:
        return env_vars[key]
    
    if key in os.environ:
        return os.environ[key]
    
    return default

def get_data_path(relative_path: Optional[str] = None, env_var_name: Optional[str] = None, default: Optional[str] = None) -> Path:
    """
    Get a resolved Path object for data files.
    
    This function constructs absolute paths based on environment variables,
    falling back to defaults relative to the project root.
    
    Args:
        relative_path: A relative path to append to the base path.
        env_var_name: The environment variable name for the base path.
        default: Default relative path if env var is not set.
    
    Returns:
        A resolved Path object.
    """
    project_root = _get_project_root()
    
    # Determine base path
    base_path_str = None
    if env_var_name:
        base_path_str = get_env_var(env_var_name)
    
    if not base_path_str:
        base_path_str = default
    
    if not base_path_str:
        # Last resort: use project root
        base_path = project_root
    else:
        base_path = Path(base_path_str)
        if not base_path.is_absolute():
            base_path = project_root / base_path
    
    # Resolve the path
    resolved_path = base_path
    if relative_path:
        resolved_path = resolved_path / relative_path
    
    # Ensure path exists (create directories if necessary)
    # Note: We don't automatically create directories here to avoid side effects
    # The caller should use ensure_directories() if creation is needed.
    
    return resolved_path.resolve()

def validate_data_paths() -> Dict[str, bool]:
    """
    Validate that all configured data paths exist.
    
    Returns:
        Dictionary mapping path names to existence status.
    """
    project_root = _get_project_root()
    
    paths_to_check = {
        "data_root": get_data_path(env_var_name=ENV_DATA_ROOT, default=DEFAULT_DATA_ROOT),
        "data_raw": get_data_path(env_var_name=ENV_DATA_RAW, default=DEFAULT_DATA_RAW),
        "data_processed": get_data_path(env_var_name=ENV_DATA_PROCESSED, default=DEFAULT_DATA_PROCESSED),
        "model_artifacts": get_data_path(env_var_name=ENV_MODEL_ARTIFACTS, default=DEFAULT_MODEL_ARTIFACTS),
        "data_figures": get_data_path(env_var_name=ENV_DATA_FIGURES, default=DEFAULT_DATA_FIGURES),
    }
    
    results = {}
    all_valid = True
    
    for name, path in paths_to_check.items():
        exists = path.exists()
        results[name] = exists
        if not exists:
            logger.warning(f"Path does not exist: {name} -> {path}")
            all_valid = False
        else:
            logger.info(f"Path valid: {name} -> {path}")
    
    if all_valid:
        logger.info("All data paths are valid.")
    else:
        logger.warning("Some data paths are missing. Please check your configuration.")
    
    return results

def setup_environment() -> Dict[str, Any]:
    """
    Full setup routine: load .env, validate paths, and return configuration.
    
    Returns:
        Dictionary containing loaded configuration and path objects.
    """
    # Load environment variables
    env_vars = load_env_vars()
    
    # Get paths
    config = {
        "project_root": _get_project_root(),
        "data_root": get_data_path(env_var_name=ENV_DATA_ROOT, default=DEFAULT_DATA_ROOT),
        "data_raw": get_data_path(env_var_name=ENV_DATA_RAW, default=DEFAULT_DATA_RAW),
        "data_processed": get_data_path(env_var_name=ENV_DATA_PROCESSED, default=DEFAULT_DATA_PROCESSED),
        "model_artifacts": get_data_path(env_var_name=ENV_MODEL_ARTIFACTS, default=DEFAULT_MODEL_ARTIFACTS),
        "data_figures": get_data_path(env_var_name=ENV_DATA_FIGURES, default=DEFAULT_DATA_FIGURES),
        "silso_url": get_env_var(ENV_SILSO_URL, default=DEFAULT_SILSO_URL),
        "sorce_url": get_env_var(ENV_SORCE_URL, default=DEFAULT_SORCE_URL),
        "env_vars": env_vars,
    }
    
    # Validate paths
    config["paths_valid"] = validate_data_paths()
    
    logger.info("Environment setup complete.")
    return config

# Convenience functions for direct import in other modules

def get_silso_url() -> str:
    """Get the SILSO data URL."""
    return get_env_var(ENV_SILSO_URL, default=DEFAULT_SILSO_URL)

def get_sorce_url() -> str:
    """Get the SORCE data URL."""
    return get_env_var(ENV_SORCE_URL, default=DEFAULT_SORCE_URL)
