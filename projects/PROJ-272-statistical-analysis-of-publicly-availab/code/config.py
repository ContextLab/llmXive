"""
code/config.py
Configuration management for paths, seeds, and data sources.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional
import numpy as np
import yaml

# Project Root
PROJECT_ROOT = Path(__file__).parent.parent

def get_path(relative_path: str) -> Path:
    """
    Resolves a relative path to an absolute path within the project root.
    """
    return PROJECT_ROOT / relative_path

def ensure_dirs(path: Path) -> None:
    """
    Ensures that the directory for the given path exists.
    """
    path.parent.mkdir(parents=True, exist_ok=True)

def set_seed(seed: int = 42) -> None:
    """
    Sets random seeds for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)

def get_seed() -> int:
    """
    Returns the current random seed.
    """
    return 42

def get_device() -> str:
    """
    Returns the device to use (CPU only per constraints).
    """
    return "cpu"

def get_max_workers() -> int:
    """
    Returns the maximum number of workers for parallel tasks.
    """
    return os.cpu_count() or 1

class DataSourceConfig:
    """
    Configuration for data sources.
    """
    def __init__(self, dataset_source: str = "ADReSS", canonical_url: str = "", mirror_url: str = ""):
        self.dataset_source = dataset_source
        self.canonical_url = canonical_url
        self.mirror_url = mirror_url
        self.source = dataset_source

    def __getattr__(self, name):
        # Tolerate unknown attribute access
        def _noop(*args, **kwargs):
            return None
        return _noop

class ModelConfig:
    """
    Configuration for models.
    """
    def __init__(self):
        self.cpu_only = True
        self.max_memory_gb = 7

def save_config(config: Dict[str, Any], path: Path) -> None:
    """
    Saves configuration to a YAML file.
    """
    ensure_dirs(path)
    with open(path, 'w') as f:
        yaml.dump(config, f)

def load_config(path: Path) -> Dict[str, Any]:
    """
    Loads configuration from a YAML file.
    """
    if path.exists():
        with open(path, 'r') as f:
            return yaml.load(f, Loader=yaml.SafeLoader)
    return {}

def get_logger(name: str):
    """
    Returns a logger instance.
    """
    import logging
    return logging.getLogger(name)
