"""
Configuration management for the molecular toxicity prediction pipeline.

This module handles environment variable management and provides standardized
paths to all project configuration files and directories.
"""
import os
from pathlib import Path
from typing import Optional

# Resolve the project root (two levels up from this file)
_CURRENT_DIR = Path(__file__).resolve().parent
_SRC_DIR = _CURRENT_DIR
PROJECT_ROOT = _SRC_DIR.parent

# Ensure environment variables are loaded with defaults if not set
def _get_env_path(var_name: str, default_rel_path: str) -> Path:
    """Get a path from an environment variable or fall back to a default relative to PROJECT_ROOT."""
    env_val = os.environ.get(var_name)
    if env_val:
        p = Path(env_val)
        if p.is_absolute():
            return p.resolve()
        # If relative env var, resolve relative to cwd (standard behavior)
        return p.resolve()
    return (PROJECT_ROOT / default_rel_path).resolve()

# Standardized directory paths
CONFIG_ROOT = _get_env_path("CONFIG_ROOT", "config")
DATA_ROOT = _get_env_path("DATA_ROOT", "data")
RESULTS_ROOT = _get_env_path("RESULTS_ROOT", "results")
MODELS_ROOT = _get_env_path("MODELS_ROOT", "models")
CODE_ROOT = PROJECT_ROOT

# Specific configuration files
STRUCTURAL_ALERTS_FILE = CONFIG_ROOT / "structural_alerts.json"
PIPELINE_CONFIG_FILE = CONFIG_ROOT / "pipeline_config.yaml"

# Ensure required directories exist
def ensure_config_dirs() -> None:
    """Create all required configuration directories if they do not exist."""
    CONFIG_ROOT.mkdir(parents=True, exist_ok=True)
    DATA_ROOT.mkdir(parents=True, exist_ok=True)
    RESULTS_ROOT.mkdir(parents=True, exist_ok=True)
    MODELS_ROOT.mkdir(parents=True, exist_ok=True)

# Initialize directories on import to ensure structure
ensure_config_dirs()

def get_config_path(filename: str) -> Path:
    """
    Get the absolute path to a configuration file.

    Args:
        filename: Name of the config file (e.g., 'structural_alerts.json')

    Returns:
        Absolute path to the config file

    Raises:
        FileNotFoundError: If the file does not exist
    """
    path = CONFIG_ROOT / filename
    if not path.exists():
        raise FileNotFoundError(f"Configuration file not found: {path}")
    return path

def get_data_path(filename: str) -> Path:
    """
    Get the absolute path to a data file.

    Args:
        filename: Name of the data file

    Returns:
        Absolute path to the data file
    """
    return DATA_ROOT / filename

def get_results_path(filename: str) -> Path:
    """
    Get the absolute path to a results file.

    Args:
        filename: Name of the results file

    Returns:
        Absolute path to the results file
    """
    return RESULTS_ROOT / filename

def get_model_path(filename: str) -> Path:
    """
    Get the absolute path to a model file.

    Args:
        filename: Name of the model file

    Returns:
        Absolute path to the model file
    """
    return MODELS_ROOT / filename

__all__ = [
    "CONFIG_ROOT",
    "DATA_ROOT",
    "RESULTS_ROOT",
    "MODELS_ROOT",
    "CODE_ROOT",
    "STRUCTURAL_ALERTS_FILE",
    "PIPELINE_CONFIG_FILE",
    "get_config_path",
    "get_data_path",
    "get_results_path",
    "get_model_path",
    "ensure_config_dirs",
    "PROJECT_ROOT",
]