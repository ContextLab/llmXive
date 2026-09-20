"""
Configuration utilities.
"""
import os
import random
import numpy as np
import torch
from typing import Optional, Dict, Any
from pathlib import Path

# Default paths relative to project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
RESULTS_ROOT = DATA_ROOT / "results"
ROUTING_CACHE_ROOT = DATA_ROOT / "routing_cache"
IMAGENET_ROOT = DATA_ROOT / "imagenet"

def ensure_directories_exist(paths: list):
    """
    Ensure the given paths exist.
    """
    for p in paths:
        if not p.exists():
            p.mkdir(parents=True, exist_ok=True)

def get_seed() -> int:
    """
    Get the random seed from environment or default.
    """
    return int(os.environ.get('RANDOM_SEED', 42))

def set_seed(seed: Optional[int] = None):
    """
    Set random seeds for reproducibility.
    """
    if seed is None:
        seed = get_seed()
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_imagenet_path() -> Path:
    """
    Get the path to the ImageNet dataset.
    """
    return IMAGENET_ROOT

def get_routing_cache_path() -> Path:
    """
    Get the path to the routing cache.
    """
    return ROUTING_CACHE_ROOT

def get_results_path() -> Path:
    """
    Get the path to the results directory.
    """
    return RESULTS_ROOT

def get_config_summary() -> Dict[str, Any]:
    """
    Get a summary of the current configuration.
    """
    return {
        "seed": get_seed(),
        "trace_set_size": os.environ.get('TRACE_SET_SIZE', 100),
        "benchmark_set_start": os.environ.get('BENCHMARK_SET_START', 100),
        "paths": {
            "data": str(DATA_ROOT),
            "results": str(RESULTS_ROOT),
            "routing_cache": str(ROUTING_CACHE_ROOT)
        }
    }
