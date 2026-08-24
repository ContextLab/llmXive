import os
import random
from typing import Dict, Any, Optional

import numpy as np

# Default configuration values
DEFAULT_CONFIG = {
    "seed": 42,
    "window_length": 60,  # seconds (Mandated by FR-003 for Schaefer 200 stability)
    "step_size": 1,       # seconds
    "fd_threshold": 0.2,  # mm (Motion exclusion threshold)
    "min_scans": 120,     # minimum number of time points
    "batch_size": 50,     # subjects per batch for memory management
    "n_surrogates": 1000, # number of phase-shuffled surrogates for null model
    "n_permutations": 10000, # permutations for significance testing
}

_config: Dict[str, Any] = {}

def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    global _config
    _config['seed'] = seed

def get_config() -> Dict[str, Any]:
    """
    Get the current configuration dictionary.
    Initializes with defaults if not yet set.
    Supports override via environment variables.
    """
    global _config
    if not _config:
        _config = DEFAULT_CONFIG.copy()
        # Allow override from environment variables if needed
        if 'WINDOW_LENGTH' in os.environ:
            _config['window_length'] = int(os.environ['WINDOW_LENGTH'])
        if 'STEP_SIZE' in os.environ:
            _config['step_size'] = int(os.environ['STEP_SIZE'])
        if 'FD_THRESHOLD' in os.environ:
            _config['fd_threshold'] = float(os.environ['FD_THRESHOLD'])
        if 'BATCH_SIZE' in os.environ:
            _config['batch_size'] = int(os.environ['BATCH_SIZE'])
        if 'N_SURROGATES' in os.environ:
            _config['n_surrogates'] = int(os.environ['N_SURROGATES'])
        if 'N_PERMUTATIONS' in os.environ:
            _config['n_permutations'] = int(os.environ['N_PERMUTATIONS'])
    return _config