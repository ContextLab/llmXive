"""
Configuration management for the project.

Provides centralized access to environment variables, project settings,
and default values for the pipeline.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Project root path (relative to current working directory)
PROJECT_ROOT = Path(__file__).parent.parent

# Default configuration values
DEFAULT_CONFIG = {
    "random_seed": 42,
    "data_split_ratio": 0.8,
    "min_rows": 50,
    "max_rows": 10000,
    "outlier_percentile": 99,
    "n_permutations": 1000,
    "model_type": "random_forest",
    "cv_folds": 5,
    "feature_importance_threshold": 0.01,
    "p_value_threshold": 0.05,
    "r2_threshold": 0.6,
}

def load_env_config() -> Dict[str, Any]:
    """
    Load configuration from environment variables.
    
    Returns:
        Dict containing configuration values from environment or defaults.
    """
    config = DEFAULT_CONFIG.copy()
    
    # Override with environment variables if present
    env_mappings = {
        "RANDOM_SEED": "random_seed",
        "DATA_SPLIT_RATIO": "data_split_ratio",
        "MIN_ROWS": "min_rows",
        "MAX_ROWS": "max_rows",
        "OUTLIER_PERCENTILE": "outlier_percentile",
        "N_PERMUTATIONS": "n_permutations",
        "MODEL_TYPE": "model_type",
        "CV_FOLDS": "cv_folds",
        "FEATURE_IMPORTANCE_THRESHOLD": "feature_importance_threshold",
        "P_VALUE_THRESHOLD": "p_value_threshold",
        "R2_THRESHOLD": "r2_threshold",
    }
    
    for env_key, config_key in env_mappings.items():
        env_value = os.getenv(env_key)
        if env_value is not None:
            # Convert to appropriate type
            if config_key in ["random_seed", "min_rows", "max_rows", 
                             "outlier_percentile", "n_permutations", "cv_folds"]:
                config[config_key] = int(env_value)
            elif config_key in ["data_split_ratio", "feature_importance_threshold",
                               "p_value_threshold", "r2_threshold"]:
                config[config_key] = float(env_value)
            else:
                config[config_key] = env_value
    
    return config

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a specific configuration value.
    
    Args:
        key: Configuration key name
        default: Default value if key not found
        
    Returns:
        Configuration value or default
    """
    config = load_env_config()
    return config.get(key, default)

def get_n_permutations() -> int:
    """Get number of permutations for statistical tests."""
    return get_config_value("n_permutations", DEFAULT_CONFIG["n_permutations"])

def get_random_seed() -> int:
    """Get random seed for reproducibility."""
    return get_config_value("random_seed", DEFAULT_CONFIG["random_seed"])

def get_data_split_ratio() -> float:
    """Get train/test split ratio."""
    return get_config_value("data_split_ratio", DEFAULT_CONFIG["data_split_ratio"])

def get_min_rows() -> int:
    """Get minimum required dataset size."""
    return get_config_value("min_rows", DEFAULT_CONFIG["min_rows"])

def get_max_rows() -> int:
    """Get maximum dataset size cap."""
    return get_config_value("max_rows", DEFAULT_CONFIG["max_rows"])

def get_outlier_percentile() -> int:
    """Get percentile for outlier clipping."""
    return get_config_value("outlier_percentile", DEFAULT_CONFIG["outlier_percentile"])

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path object pointing to project root
    """
    return PROJECT_ROOT
