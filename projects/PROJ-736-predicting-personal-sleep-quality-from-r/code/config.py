"""Configuration for sleep quality prediction pipeline."""
import os
import random
from pathlib import Path
from typing import Dict, Any, Union

import numpy as np


def get_paths() -> Dict[str, str]:
    """Get project directory paths."""
    base = Path(__file__).parent.parent
    return {
        "root": str(base),
        "code_dir": str(base / "code"),
        "data_dir": str(base / "data"),
        "raw_dir": str(base / "data" / "raw"),
        "processed_dir": str(base / "data" / "processed"),
        "results_dir": str(base / "data" / "results"),
        "logs_dir": str(base / "data" / "logs"),
        "figures_dir": str(base / "data" / "figures"),
    }


def ensure_dirs() -> None:
    """Create all required directories."""
    paths = get_paths()
    for path in paths.values():
        os.makedirs(path, exist_ok=True)


def set_seeds(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)


def get_hyperparameter(name: str, default: Any = None) -> Any:
    """Get hyperparameter from config or return default."""
    # Hyperparameters can be loaded from a config file or environment
    # For now, return defaults
    defaults = {
        "random_seed": 42,
        "cv_splits": 5,
        "permutation_count": 1000,
        "sensitivity_timeout_hours": 3,
        "global_timeout_hours": 5,
        "expected_r2_effect_size": 0.05,
        "power_threshold": 0.8,
        "l1_ratio_grid": [0.1, 0.5, 0.9],
        "alpha_grid": list(np.logspace(-4, 0, 10)),
        "ram_limit_gb": 6,
    }
    return defaults.get(name, default)
