"""
Configuration management for the project.
Provides centralized access to environment variables and default values.
"""
import os
from pathlib import Path
from typing import Any, Dict, Optional

# Project root is the parent of the 'code' directory
# Assuming this file is at: projects/PROJ-240-.../code/config.py
_PROJECT_ROOT = Path(__file__).resolve().parent.parent

def get_project_root() -> Path:
    """Return the root directory of the project."""
    return _PROJECT_ROOT

def get_config_value(key: str, default: Any = None) -> Any:
    """Get a configuration value from environment variables or defaults."""
    return os.environ.get(key, default)

def get_min_rows() -> int:
    """Minimum number of rows required for valid processing."""
    return int(get_config_value("MIN_ROWS", 50))

def get_max_rows() -> int:
    """Maximum number of rows allowed (hard cap for memory/scalability)."""
    return int(get_config_value("MAX_ROWS", 10000))

def get_outlier_percentile() -> float:
    """Percentile threshold for outlier clipping (e.g., 99)."""
    return float(get_config_value("OUTLIER_PERCENTILE", 99))

def get_n_permutations() -> int:
    """Number of permutations for statistical tests."""
    return int(get_config_value("N_PERMUTATIONS", 1000))

def get_random_seed() -> int:
    """Random seed for reproducibility."""
    return int(get_config_value("SEED", 42))

def get_data_split_ratio() -> float:
    """Ratio of training data (e.g., 0.8 for 80% train, 20% test)."""
    return float(get_config_value("DATA_SPLIT_RATIO", 0.8))

def load_env_config() -> Dict[str, Any]:
    """Load all relevant environment variables into a dictionary."""
    return {
        "MIN_ROWS": get_min_rows(),
        "MAX_ROWS": get_max_rows(),
        "OUTLIER_PERCENTILE": get_outlier_percentile(),
        "N_PERMUTATIONS": get_n_permutations(),
        "SEED": get_random_seed(),
        "DATA_SPLIT_RATIO": get_data_split_ratio(),
    }
