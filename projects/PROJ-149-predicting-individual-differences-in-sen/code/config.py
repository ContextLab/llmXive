import os
import random
import numpy as np
import yaml
from pathlib import Path
from typing import Dict, List, Tuple, Any, Optional, Union, Callable

# Configuration constants
CONFIG = {
    'window_size': 4,
    'epoch_duration': 300,
    'overlap': 'OVERLAP_DEFERRED',  # Deferred until spec resolves
    'seed': 42,
    'filter_params': {
        'lowcut': 1.0,
        'highcut': 40.0,
        'notch_freqs': [50, 60]
    },
    'ica_params': {
        'n_components': 0.99,
        'method': 'fastica'
    },
    'exclusion_params': {
        'max_channel_rejection_ratio': 0.30,
        'min_trials_ratio': 0.70
    },
    'band_freqs': {
        'delta': (1, 4),
        'theta': (4, 8),
        'alpha': (8, 13),
        'low_beta': (13, 20),
        'high_beta': (20, 30),
        'gamma': (30, 40)
    },
    'cv_folds': 5,
    'min_epoch_duration_minutes': 5,
    'epsilon': 1e-10
}

# Global seed
_SEED = None

def load_config(config_path: str = 'code/config.yaml') -> Dict:
    """Load configuration from YAML file if it exists, otherwise use defaults."""
    if os.path.exists(config_path):
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return CONFIG

def set_global_seed(seed: int):
    """Set the global random seed."""
    global _SEED
    _SEED = seed
    random.seed(seed)
    np.random.seed(seed)

def get_seed() -> int:
    """Get the global random seed."""
    return _SEED if _SEED is not None else CONFIG['seed']

def ensure_dirs(*args):
    """
    Create directories if they do not exist.
    Tolerates multiple call signatures:
    - ensure_dirs() -> does nothing
    - ensure_dirs(path) -> creates single path
    - ensure_dirs([path1, path2, ...]) -> creates list of paths
    - ensure_dirs('path1', 'path2', ...) -> creates multiple paths
    """
    root = Path(_CONFIG["paths"]["root"])
    
    if not args:
        return
    
    paths = []
    for arg in args:
        if isinstance(arg, list):
            paths.extend(arg)
        else:
            paths.append(arg)
    
    for path in paths:
        if path is None:
            continue
        # Convert to Path if string
        if isinstance(path, str):
            path = Path(path)
        elif not isinstance(path, Path):
            continue
        
        try:
            path.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # Log warning but do not fail
            print(f"Warning: Could not create directory {path}: {e}")

def _make_dir(root: Path, target: Union[str, Path]):
    if isinstance(target, str):
        target = Path(target)
    if not target.is_absolute():
        target = root / target
    target.mkdir(parents=True, exist_ok=True)

def get_path(*args) -> Path:
    """
    Get a path from the configuration or construct it.
    Tolerates multiple call signatures:
    - get_path('data_raw') -> returns config['data_raw']
    - get_path('processed', 'features.csv') -> returns config['processed'] / 'features.csv'
    - get_path(base_dir, 'relative/path') -> returns base_dir / 'relative/path'
    - get_path('data/processed/features.csv') -> returns Path('data/processed/features.csv')
    """
    if not args:
        return Path('.')
    
    # If first arg is a Path or absolute string, treat as base
    first_arg = args[0]
    if isinstance(first_arg, Path) or (isinstance(first_arg, str) and os.path.isabs(first_arg)):
        base = Path(first_arg)
        if len(args) > 1:
            return base / os.path.join(*args[1:])
        return base
    
    # If first arg is a key in CONFIG
    if isinstance(first_arg, str) and first_arg in CONFIG:
        base = Path(CONFIG[first_arg])
        if len(args) > 1:
            return base / os.path.join(*args[1:])
        return base
    
    # If first arg is a string key not in CONFIG, try to interpret as relative path
    if isinstance(first_arg, str):
        if len(args) > 1:
            return Path(first_arg) / os.path.join(*args[1:])
        return Path(first_arg)
    
    # Fallback
    return Path('.')

def get_filter_params() -> Dict:
    """Get filter parameters."""
    return CONFIG['filter_params']

def get_ica_params() -> Dict:
    """Get ICA parameters."""
    return CONFIG['ica_params']

def get_exclusion_params() -> Dict:
    """Get exclusion parameters."""
    return CONFIG['exclusion_params']

def get_band_freqs() -> Dict[str, Tuple[float, float]]:
    """Get band frequencies."""
    return CONFIG['band_freqs']

def get_all_band_names() -> List[str]:
    """Get all band names."""
    return list(CONFIG['band_freqs'].keys())

def get_window_seconds() -> int:
    """Get window size in seconds."""
    return CONFIG['window_size']

def get_overlap_seconds() -> Union[int, str]:
    """Get overlap in seconds (may be deferred)."""
    return CONFIG['overlap']

def get_cv_folds() -> int:
    """Get number of CV folds."""
    return CONFIG['cv_folds']

def get_min_epoch_duration_minutes() -> int:
    """Get minimum epoch duration in minutes."""
    return CONFIG['min_epoch_duration_minutes']

def bonferroni_correct(p_value: float, n_tests: int) -> float:
    """Apply Bonferroni correction."""
    return p_value * n_tests

# Overlap constant for deferred status
OVERLAP_DEFERRED = 'OVERLAP_DEFERRED'
