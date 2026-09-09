import os
from pathlib import Path
from typing import Any, Dict, Optional

def get_project_root() -> Path:
    """
    Get the project root directory.
    Assumes the script is run from the project root or a subdirectory.
    """
    # Try to find the project root by looking for a marker file or directory
    current = Path(__file__).resolve()
    while current.parent != current:
        if (current / "project_marker.txt").exists():
            return current
        current = current.parent
    
    # Fallback to current working directory
    return Path.cwd()

def get_config_value(key: str, default: Any = None) -> Any:
    """
    Get a configuration value from environment variables or defaults.
    """
    return os.environ.get(key, default)

def get_min_rows() -> int:
    """
    Get the minimum number of rows required for the dataset.
    """
    return int(get_config_value('MIN_ROWS', 50))

def get_max_rows() -> int:
    """
    Get the maximum number of rows allowed for the dataset.
    """
    return int(get_config_value('MAX_ROWS', 10000))

def get_outlier_percentile() -> float:
    """
    Get the percentile threshold for outlier clipping.
    """
    return float(get_config_value('OUTLIER_PERCENTILE', 99.0))

def get_n_permutations() -> int:
    """
    Get the number of permutations for statistical tests.
    """
    return int(get_config_value('N_PERMUTATIONS', 1000))

def get_random_seed() -> int:
    """
    Get the random seed for reproducibility.
    """
    return int(get_config_value('RANDOM_SEED', 42))

def get_data_split_ratio() -> float:
    """
    Get the train/test split ratio.
    """
    return float(get_config_value('DATA_SPLIT_RATIO', 0.8))

def load_env_config() -> Dict[str, Any]:
    """
    Load all environment configuration variables.
    """
    return {
        'MIN_ROWS': get_min_rows(),
        'MAX_ROWS': get_max_rows(),
        'OUTLIER_PERCENTILE': get_outlier_percentile(),
        'N_PERMUTATIONS': get_n_permutations(),
        'RANDOM_SEED': get_random_seed(),
        'DATA_SPLIT_RATIO': get_data_split_ratio()
    }
