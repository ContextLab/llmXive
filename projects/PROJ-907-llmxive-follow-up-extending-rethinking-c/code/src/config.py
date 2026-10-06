import os
import random
import numpy as np
import torch
from typing import Optional, Dict, Any
from pathlib import Path

def ensure_directories_exist():
    """Ensures all required directories exist."""
    dirs = [
        "data/routing_cache",
        "data/results",
        "data/imagenet_trace",
        "data/imagenet_benchmark",
        "data/routing_cache",
        "state/projects/PROJ-907-llmxive-follow-up-extending-rethinking-c"
    ]
    for d in dirs:
        Path(d).mkdir(parents=True, exist_ok=True)

def get_seed() -> int:
    """Returns the random seed from environment or default."""
    return int(os.getenv('RANDOM_SEED', '42'))

def set_seed(seed: int):
    """Sets the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_imagenet_path() -> str:
    """Returns the path to the ImageNet dataset."""
    return os.getenv('IMAGENET_PATH', 'data/imagenet')

def get_routing_cache_path() -> str:
    """Returns the path to the routing cache directory."""
    return os.getenv('ROUTING_CACHE_PATH', 'data/routing_cache')

def get_results_path() -> str:
    """Returns the path to the results directory."""
    return os.getenv('RESULTS_PATH', 'data/results')

def get_config_summary() -> Dict[str, Any]:
    """Returns a summary of the current configuration."""
    return {
        "trace_set_size": int(os.getenv('TRACE_SET_SIZE', '100')),
        "benchmark_set_size": int(os.getenv('BENCHMARK_SET_SIZE', '100')),
        "benchmark_set_start": int(os.getenv('BENCHMARK_SET_START', '100')),
        "random_seed": get_seed(),
        "num_timesteps": int(os.getenv('NUM_TIMESTEPS', '1000')),
        "fid_weights_version": os.getenv('FID_WEIGHTS_VERSION', 'IMAGENET1K_V1'),
        "torchvision_version": os.getenv('TORCHVISION_VERSION', '0.18.0'),
        "benchmark_seeds": os.getenv('BENCHMARK_SEEDS', '[]'),
        "sensitivity_thresholds": os.getenv('SENSITIVITY_THRESHOLDS', '[]'),
        "sensitivity_set_size": int(os.getenv('SENSITIVITY_SET_SIZE', '100'))
    }
