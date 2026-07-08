"""
Configuration management for the AI Personality Consistency research pipeline.

Handles environment variable loading, fallback model configurations, and
project path resolution.
"""
import os
from pathlib import Path
from typing import Optional, Dict, Any

# Base project directory (assumed to be run from project root or code/ subdirectory)
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Default configuration values
DEFAULTS = {
    "MODEL_NAME": "distilbert-base-uncased",
    "MODEL_FALLBACK": "bert-base-uncased",
    "MAX_BATCH_SIZE": 32,
    "MAX_MEMORY_GB": 7.0,
    "DEVICE": "cpu",
    "LOG_LEVEL": "INFO",
    "DATA_RAW_DIR": "data/raw",
    "DATA_PROCESSED_DIR": "data/processed",
    "OUTPUT_FIGURES_DIR": "output/figures",
    "OUTPUT_REPORTS_DIR": "output/reports",
    "HF_DATASET_NAME": "DailyDialog",
    "HF_DATASET_SPLIT": "train",
}

# Environment variable names mapped to config keys
ENV_MAP = {
    "MODEL_NAME": "RESEARCH_MODEL_NAME",
    "MODEL_FALLBACK": "RESEARCH_MODEL_FALLBACK",
    "MAX_BATCH_SIZE": "RESEARCH_MAX_BATCH_SIZE",
    "MAX_MEMORY_GB": "RESEARCH_MAX_MEMORY_GB",
    "DEVICE": "RESEARCH_DEVICE",
    "LOG_LEVEL": "RESEARCH_LOG_LEVEL",
    "DATA_RAW_DIR": "RESEARCH_DATA_RAW_DIR",
    "DATA_PROCESSED_DIR": "RESEARCH_DATA_PROCESSED_DIR",
    "OUTPUT_FIGURES_DIR": "RESEARCH_OUTPUT_FIGURES_DIR",
    "OUTPUT_REPORTS_DIR": "RESEARCH_OUTPUT_REPORTS_DIR",
    "HF_DATASET_NAME": "RESEARCH_HF_DATASET_NAME",
    "HF_DATASET_SPLIT": "RESEARCH_HF_DATASET_SPLIT",
}


def load_env_vars() -> Dict[str, str]:
    """
    Load environment variables from .env file if present, otherwise use system env.

    Returns:
        Dictionary of environment variables.
    """
    env_file = _PROJECT_ROOT / ".env"
    if env_file.exists():
        try:
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#") and "=" in line:
                        key, value = line.split("=", 1)
                        os.environ[key.strip()] = value.strip()
        except Exception:
            pass  # Silently ignore .env errors, fall back to system env

    return dict(os.environ)


def get_config(key: str, default: Optional[Any] = None) -> Any:
    """
    Retrieve a configuration value.

    Priority:
        1. Environment variable (if defined in ENV_MAP)
        2. Default value from DEFAULTS
        3. Provided default argument

    Args:
        key: Configuration key name.
        default: Fallback default if not found elsewhere.

    Returns:
        The configuration value.
    """
    env_key = ENV_MAP.get(key)
    if env_key and env_key in os.environ:
        val = os.environ[env_key]
        # Type conversion for numeric values
        if key in ("MAX_BATCH_SIZE",):
            try:
                return int(val)
            except ValueError:
                pass
        if key in ("MAX_MEMORY_GB",):
            try:
                return float(val)
            except ValueError:
                pass
        return val

    if key in DEFAULTS:
        return DEFAULTS[key]

    return default


def get_model_config() -> Dict[str, str]:
    """
    Get the full model configuration including fallback logic.

    Returns:
        Dictionary with 'primary' and 'fallback' model names.
    """
    return {
        "primary": get_config("MODEL_NAME"),
        "fallback": get_config("MODEL_FALLBACK"),
        "device": get_config("DEVICE"),
    }


def get_path(key: str) -> Path:
    """
    Resolve a project path relative to the project root.

    Args:
        key: Configuration key for the path (e.g., 'DATA_RAW_DIR').

    Returns:
        Absolute Path object.
    """
    relative = get_config(key)
    return _PROJECT_ROOT / relative


def get_data_paths() -> Dict[str, Path]:
    """
    Get all data-related paths.

    Returns:
        Dictionary with 'raw' and 'processed' Path objects.
    """
    return {
        "raw": get_path("DATA_RAW_DIR"),
        "processed": get_path("DATA_PROCESSED_DIR"),
    }


def get_output_paths() -> Dict[str, Path]:
    """
    Get all output-related paths.

    Returns:
        Dictionary with 'figures' and 'reports' Path objects.
    """
    return {
        "figures": get_path("OUTPUT_FIGURES_DIR"),
        "reports": get_path("OUTPUT_REPORTS_DIR"),
    }


# Initialize configuration on module load
_CONFIG = load_env_vars()

# Convenience accessors
model_config = get_model_config()
data_paths = get_data_paths()
output_paths = get_output_paths()
log_level = get_config("LOG_LEVEL")
max_batch_size = get_config("MAX_BATCH_SIZE")
max_memory_gb = get_config("MAX_MEMORY_GB")
hf_dataset_name = get_config("HF_DATASET_NAME")
hf_dataset_split = get_config("HF_DATASET_SPLIT")