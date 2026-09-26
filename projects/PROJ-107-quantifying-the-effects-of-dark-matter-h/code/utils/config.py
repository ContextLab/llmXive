import os
import random
from pathlib import Path
from typing import Any, Dict
import yaml

# Project root is the directory containing 'code', 'data', etc.
# Assuming this file is at code/utils/config.py
_PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

def get_project_root() -> Path:
    """Return the root directory of the project."""
    return _PROJECT_ROOT

def get_data_raw_path() -> Path:
    """Return the path to the raw data directory."""
    return get_project_root() / "data" / "raw"

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
    return get_project_root() / "data" / "raw" / "millennium"

def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load configuration from a YAML file."""
    if config_path is None:
        config_path = get_project_root() / "config.yaml"
    
    if config_path.exists():
        with open(config_path, 'r') as f:
            return yaml.safe_load(f)
    return {}

def set_random_seed(seed: int = 42) -> None:
    """Set random seed for reproducibility."""
    random.seed(seed)
    try:
        import numpy as np
        np.random.seed(seed)
    except ImportError:
        pass
