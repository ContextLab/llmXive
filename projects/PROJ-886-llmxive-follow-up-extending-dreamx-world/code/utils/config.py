import os
import random
import logging
from typing import Optional, Dict, Any
import torch
import numpy as np
from pathlib import Path

def set_global_seed(seed: int = 42):
    """Set global random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_env_config() -> Dict[str, Any]:
    """Load configuration from environment variables."""
    return {
        'seed': int(os.getenv('RANDOM_SEED', 42)),
        'device': os.getenv('DEVICE', 'cpu'),
        'data_path': os.getenv('DATA_PATH', 'data'),
    }

def ensure_directories(paths: list):
    """Ensure all specified directories exist."""
    for path in paths:
        Path(path).mkdir(parents=True, exist_ok=True)

def init_environment(seed: int = 42):
    """Initialize the environment with default settings."""
    set_global_seed(seed)
    config = get_env_config()
    ensure_directories([
        'data/raw',
        'data/derived',
        'data/derived/videos',
        'logs',
        'figures',
        'code',
        'code/models',
        'code/pipeline',
        'code/analysis',
        'code/utils',
        'tests/unit',
        'tests/integration'
    ])
    return config
