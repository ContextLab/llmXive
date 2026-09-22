"""
Configuration management for the project.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

def get_project_root() -> Path:
    """Return the project root directory."""
    # Assumes this file is at project_root/code/config.py
    return Path(__file__).resolve().parent.parent

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a configuration value from environment variables or defaults.
    """
    defaults = {
        "N_ROWS_TARGET": 10000,
        "N_PERMUTATIONS": 1000,
        "SEED": 42,
        "OUTLIER_PERCENTILE": 0.99,
        "N_ESTIMATORS": 100,
        "DATA_SPLIT_RATIO": 0.2,
    }
    return int(os.getenv(key, defaults.get(key, default)))

def get_random_seed() -> int:
    return get_config_value("SEED", 42)

def get_max_rows() -> int:
    return get_config_value("N_ROWS_TARGET", 10000)

def get_min_rows() -> int:
    return 50

def get_outlier_percentile() -> float:
    return get_config_value("OUTLIER_PERCENTILE", 0.99)

def get_n_permutations() -> int:
    return get_config_value("N_PERMUTATIONS", 1000)

def get_n_estimators() -> int:
    return get_config_value("N_ESTIMATORS", 100)

def get_data_split_ratio() -> float:
    return get_config_value("DATA_SPLIT_RATIO", 0.2)

def load_env_config() -> Dict[str, Any]:
    """Load all config values into a dictionary."""
    return {
        "N_ROWS_TARGET": get_max_rows(),
        "N_PERMUTATIONS": get_n_permutations(),
        "SEED": get_random_seed(),
        "OUTLIER_PERCENTILE": get_outlier_percentile(),
        "N_ESTIMATORS": get_n_estimators(),
        "DATA_SPLIT_RATIO": get_data_split_ratio(),
    }