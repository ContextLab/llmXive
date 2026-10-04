import os
import random
import numpy as np
from pathlib import Path
from typing import Any, Dict, Optional
import yaml

# Project root is the directory containing 'code', 'data', etc.
# Assuming this file is at code/utils/config.py
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Global random seed state
_RANDOM_SEED = 42

def get_project_root() -> Path:
    """Return the root directory of the project."""
    return _PROJECT_ROOT

def get_data_raw_path() -> Path:
    """Return the path to the raw data directory."""
    raw = get_project_root() / "data" / "raw"
    raw.mkdir(parents=True, exist_ok=True)
    return raw

def get_data_processed_path() -> Path:
    """Return the path to the processed data directory."""
    processed = get_project_root() / "data" / "processed"
    processed.mkdir(parents=True, exist_ok=True)
    return processed

def get_output_path() -> Path:
    """Return the path to the output directory (for figures/reports)."""
    output = get_project_root() / "outputs"
    output.mkdir(parents=True, exist_ok=True)
    return output

def get_figures_path() -> Path:
    """Return the path to the figures directory."""
    figures = get_project_root() / "figures"
    figures.mkdir(parents=True, exist_ok=True)
    return figures

def get_millennium_path() -> Path:
    """Return the path to the millennium data directory."""
    millennium = get_project_root() / "data" / "raw" / "millennium"
    millennium.mkdir(parents=True, exist_ok=True)
    return millennium

def get_logs_path() -> Path:
    """Return the path to the logs directory."""
    logs = get_project_root() / "outputs" / "logs"
    logs.mkdir(parents=True, exist_ok=True)
    return logs

def get_state_path() -> Path:
    """Return the path to the state directory."""
    state = get_project_root() / "state"
    state.mkdir(parents=True, exist_ok=True)
    return state

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    if config_path is None:
        config_path = get_project_root() / "config.yaml"
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def set_random_seed(seed: int = 42) -> None:
    """Set random seed for reproducibility for random and numpy."""
    global _RANDOM_SEED
    _RANDOM_SEED = seed
    random.seed(seed)
    try:
        np.random.seed(seed)
    except ImportError:
        pass

def get_random_seed() -> int:
    """Get the current random seed."""
    return _RANDOM_SEED

# Constants for data processing limits (from project constraints)
MAX_RAM_GB = 7.0
MAX_DISK_GB = 14.0
CHUNK_SIZE_MB = 100  # Default chunk size for processing
MIN_PARTICLE_COUNT = 10000  # Minimum particles for valid halo analysis
