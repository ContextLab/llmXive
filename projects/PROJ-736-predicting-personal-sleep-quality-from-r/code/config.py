"""Configuration module for the sleep quality prediction project."""
import os
import random
from pathlib import Path
from typing import Dict, Any, Union

# Project root
PROJECT_ROOT = Path(__file__).parent.parent

# Seeds for reproducibility
RANDOM_SEED = 42
NUMPY_SEED = 42

# Hyperparameters
VARIANCE_THRESHOLD = 0.01
PCA_RETENTION = 0.95
SUBSET_SIZE = 100

# Permutation test parameters
PERMUTATION_COUNT = 1000
PERMUTATION_SUBSET_SIZE = 100

# Timeout limits (hours)
SENSITIVITY_TIMEOUT_HOURS = 3
GLOBAL_TIMEOUT_HOURS = 5

# Statistical parameters
EXPECTED_R2_EFFECT_SIZE = 0.05
POWER_THRESHOLD = 0.8
ALPHA_LEVEL = 0.05

# RAM limit (GB)
RAM_LIMIT_GB = 6

# CPU cores
CPU_CORES = 1


def get_paths() -> Dict[str, Union[str, Path]]:
    """Get all project paths."""
    base = PROJECT_ROOT
    return {
        "root": base,
        "code": base / "code",
        "data": base / "data",
        "data_raw": base / "data" / "raw",
        "data_processed": base / "data" / "processed",
        "data_results": base / "data" / "results",
        "data_logs": base / "data" / "logs",
        "raw_dir": base / "data" / "raw",
        "processed_dir": base / "data" / "processed",
        "results_dir": base / "data" / "results",
        "figures_dir": base / "data" / "figures",
        "behavioral_dir": base / "data" / "raw" / "behavioral",
    }


def ensure_dirs() -> None:
    """Ensure all required directories exist."""
    paths = get_paths()
    for key, path in paths.items():
        if isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)
        else:
            os.makedirs(path, exist_ok=True)


def get_hyperparameter(name: str) -> Any:
    """Get a hyperparameter by name."""
    params = {
        "variance_threshold": VARIANCE_THRESHOLD,
        "pca_retention": PCA_RETENTION,
        "subset_size": SUBSET_SIZE,
        "permutation_count": PERMUTATION_COUNT,
        "permutation_subset_size": PERMUTATION_SUBSET_SIZE,
        "sensitivity_timeout_hours": SENSITIVITY_TIMEOUT_HOURS,
        "global_timeout_hours": GLOBAL_TIMEOUT_HOURS,
        "expected_r2_effect_size": EXPECTED_R2_EFFECT_SIZE,
        "power_threshold": POWER_THRESHOLD,
        "alpha_level": ALPHA_LEVEL,
        "ram_limit_gb": RAM_LIMIT_GB,
        "cpu_cores": CPU_CORES,
    }
    return params.get(name)


def set_seeds() -> None:
    """Set random seeds for reproducibility."""
    random.seed(RANDOM_SEED)
    import numpy as np
    np.random.seed(NUMPY_SEED)
