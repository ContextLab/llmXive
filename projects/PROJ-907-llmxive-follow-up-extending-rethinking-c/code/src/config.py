import os
import random
import numpy as np
import torch
from typing import Optional, Dict, Any
from pathlib import Path

def ensure_directories_exist():
    """
    Creates necessary directories if they don't exist.
    """
    dirs = [
        'data/imagenet_trace',
        'data/imagenet_benchmark',
        'data/routing_cache',
        'data/results',
        'docs'
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def get_seed() -> int:
    """
    Returns the random seed from environment variable or default.
    """
    return int(os.getenv('RANDOM_SEED', '42'))

def set_seed(seed: int):
    """
    Sets the random seed for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_imagenet_path() -> str:
    """
    Returns the path to ImageNet data.
    """
    return os.getenv('IMAGENET_PATH', 'data/imagenet')

def get_routing_cache_path() -> str:
    """
    Returns the path to routing cache.
    """
    return os.getenv('ROUTING_CACHE_PATH', 'data/routing_cache')

def get_results_path() -> str:
    """
    Returns the path to results.
    """
    return os.getenv('RESULTS_PATH', 'data/results')

def get_config_summary() -> Dict[str, Any]:
    """
    Returns a summary of the current configuration.
    """
    return {
        "seed": get_seed(),
        "imagenet_path": get_imagenet_path(),
        "routing_cache_path": get_routing_cache_path(),
        "results_path": get_results_path()
    }
