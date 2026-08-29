"""
code/config.py
Central configuration for the project.
Defines paths, filter parameters, ICA settings, and exclusion thresholds.
"""
import os
import sys
from pathlib import Path
from typing import Union, List, Any, Optional

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent
DATA_ROOT = PROJECT_ROOT / 'data'
CODE_ROOT = PROJECT_ROOT / 'code'

# Constants
EPSILON = 1e-9
OVERLAP = 0.5
WINDOW_SIZE = 4  # Spec FR-003 mandates 4s windows
POLY_DEGREE = 2
SEED = 42

def get_path(*parts: str) -> Path:
    """
    Flexible path resolver.
    Accepts:
      - get_path("interim", "file.csv") -> data/interim/file.csv
      - get_path("data/interim", "file.csv") -> data/interim/file.csv
      - get_path("processed", "model.json") -> data/processed/model.json
    """
    # Flatten parts
    full_path = os.path.join(*parts)
    
    # Check if it's an absolute path or starts with data/
    if os.path.isabs(full_path):
        return Path(full_path)
    
    if full_path.startswith('data/'):
        return DATA_ROOT / full_path[5:]
    
    # Assume relative to data/ if not specified otherwise
    # Handle common prefixes
    if full_path.startswith('interim/') or full_path.startswith('processed/') or full_path.startswith('raw/'):
        return DATA_ROOT / full_path
    
    # Default to data/interim if ambiguous, but try to match common usage
    # If it looks like a filename, put in interim
    if '.' in full_path and '/' not in full_path:
        return DATA_ROOT / 'interim' / full_path
    
    return DATA_ROOT / full_path

def ensure_dirs(*paths: Union[str, Path, List[Union[str, Path]]]) -> None:
    """
    Create directories for given paths.
    Accepts multiple arguments, strings, Path objects, or lists of them.
    """
    import os
    import pathlib
    
    def _process(p):
        if isinstance(p, list):
            for item in p:
                _process(item)
        else:
            path_obj = pathlib.Path(p) if not isinstance(p, pathlib.Path) else p
            path_obj.mkdir(parents=True, exist_ok=True)
    
    _process(paths)

def get_filter_params() -> dict:
    """
    Returns filter parameters.
    """
    return {
        'l_freq': 1.0,
        'h_freq': 45.0,
        'notch_freqs': [50.0, 60.0] # Support 50/60 Hz
    }

def get_ica_params() -> dict:
    """
    Returns ICA parameters.
    """
    return {
        'n_components': 0.95,
        'max_iter': 500
    }

def get_exclusion_params() -> dict:
    """
    Returns exclusion parameters.
    """
    return {
        'variance_threshold_std': 3.0,
        'max_rejected_ratio': 0.30,
        'min_epoch_duration_min': 5.0 # 5 minutes
    }

def get_band_freqs() -> dict:
    """
    Returns canonical frequency bands.
    """
    return {
        'delta': (1.0, 4.0),
        'theta': (4.0, 8.0),
        'alpha': (8.0, 13.0),
        'low_beta': (13.0, 20.0),
        'high_beta': (20.0, 30.0),
        'gamma': (30.0, 45.0)
    }

def get_all_band_names() -> list:
    """
    Returns list of band names.
    """
    return list(get_band_freqs().keys())

def get_cv_folds() -> int:
    """
    Returns number of CV folds.
    """
    return 5

def get_epsilon() -> float:
    """
    Returns epsilon for numerical stability.
    """
    return EPSILON

def get_seed() -> int:
    """
    Returns random seed.
    """
    return SEED
