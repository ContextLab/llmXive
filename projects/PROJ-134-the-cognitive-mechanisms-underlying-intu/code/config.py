import os
from pathlib import Path
import random
import numpy as np
import yaml

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directory paths (relative to PROJECT_ROOT)
DIRS = {
    "code": "code",
    "data": "data",
    "tests": "tests",
    "state": "state",
    "data_raw": "data/raw",
    "data_processed": "data/processed",
    "data_logs": "data/logs",
    "reports": "reports",
    "figures": "figures"
}

# Random seed for reproducibility
RANDOM_SEED = 42

# Data Mode Configuration
# Options: 'simulation' | 'real'
# Default: 'simulation'
# If set to 'real', the pipeline will attempt to fetch real data from OSF/HuggingFace
# and will fail loudly if the fetch fails (no synthetic fallback).
DATA_MODE = os.getenv('DATA_MODE', 'simulation')

# Statistical Constants
ALPHA = 0.05
BONFERRONI_CORRECTION_FACTOR = 1  # Will be updated dynamically based on number of tests

# Model Hyperparameters (Simulation Only for now)
GROUND_TRUTH_EFFECT_SIZE = 0.5  # Known effect size for simulation validation

def ensure_directories():
    """Create all required directories if they don't exist."""
    for dir_name in DIRS.values():
        dir_path = PROJECT_ROOT / dir_name
        dir_path.mkdir(parents=True, exist_ok=True)

def init_random_seeds(seed: int = RANDOM_SEED):
    """Initialize random seeds for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
    except ImportError:
        pass  # PyTorch not installed

def validate_data_mode():
    """
    Validates the DATA_MODE configuration.
    Raises ValueError if DATA_MODE is not 'simulation' or 'real'.
    """
    valid_modes = ['simulation', 'real']
    if DATA_MODE not in valid_modes:
        raise ValueError(f"Invalid DATA_MODE '{DATA_MODE}'. Must be one of {valid_modes}")
    return True

def get_path(relative_path: str) -> Path:
    """
    Resolve a relative path to an absolute path within the project root.
    
    Args:
        relative_path: Path relative to PROJECT_ROOT (e.g., 'data/processed/output.csv')
    
    Returns:
        Absolute Path object
    """
    return PROJECT_ROOT / relative_path

def load_yaml_config(file_path: str) -> dict:
    """
    Load a YAML configuration file.
    
    Args:
        file_path: Relative path to the YAML file (e.g., 'data/config/unity_blend_shapes.yaml')
    
    Returns:
        Dictionary containing the configuration
    """
    full_path = get_path(file_path)
    if not full_path.exists():
        raise FileNotFoundError(f"Config file not found: {full_path}")
    
    with open(full_path, 'r') as f:
        return yaml.safe_load(f)