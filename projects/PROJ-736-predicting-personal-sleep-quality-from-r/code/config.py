import os
import random
from pathlib import Path
from typing import Dict, Any
import numpy as np

# Global config state
_config = {
    'seed': 42,
    'variance_threshold': 0.01,
    'pca_retention': 0.95,
    'subset_size': 100,
    'n_splits_outer': 5,
    'n_splits_inner': 3,
    'elasticnet_l1_ratio': 0.5,
    'elasticnet_max_iter': 10000,
}


def set_all_seeds(seed: int = 42) -> None:
    """Set random seeds for reproducibility."""
    _config['seed'] = seed
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)


def get_paths() -> Dict[str, Path]:
    """Get all project paths."""
    project_root = Path(__file__).parent.parent
    return {
        'project_root': project_root,
        'code_dir': project_root / 'code',
        'data_dir': project_root / 'data',
        'raw_dir': project_root / 'data' / 'raw',
        'behavioral_dir': project_root / 'data' / 'raw' / 'behavioral',
        'cifti_dir': project_root / 'data' / 'raw' / 'cifti',
        'processed_dir': project_root / 'data' / 'processed',
        'results_dir': project_root / 'data' / 'results',
        'logs_dir': project_root / 'data' / 'logs',
        'tests_dir': project_root / 'tests',
    }


def get_hyperparameter(key: str) -> Any:
    """Get a hyperparameter value."""
    return _config.get(key)


def update_hyperparameter(key: str, value: Any) -> None:
    """Update a hyperparameter."""
    _config[key] = value


def ensure_dirs() -> None:
    """Ensure all project directories exist."""
    paths = get_paths()
    for path in paths.values():
        if isinstance(path, Path):
            path.mkdir(parents=True, exist_ok=True)


def get_config_summary() -> Dict[str, Any]:
    """Get current configuration summary."""
    return {
        'seed': _config['seed'],
        'variance_threshold': _config['variance_threshold'],
        'pca_retention': _config['pca_retention'],
        'subset_size': _config['subset_size'],
        'paths': {k: str(v) for k, v in get_paths().items()},
    }
