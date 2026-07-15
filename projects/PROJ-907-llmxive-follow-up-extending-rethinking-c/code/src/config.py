import os
import random
import numpy as np
import torch
from typing import Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Environment variable names
ENV_IMAGENET_PATH = "IMAGENET_PATH"
ENV_SEED = "LLMXIVE_SEED"
ENV_ROUTING_CACHE = "ROUTING_CACHE_PATH"
ENV_RESULTS = "RESULTS_PATH"

def _get_env_or_default(key: str, default: str) -> str:
    """Retrieves environment variable or returns default. Logs the value."""
    val = os.environ.get(key, default)
    logger.debug(f"Config: {key} = {val}")
    return val

def set_seed(seed: Optional[int] = None):
    """
    Sets random seeds for reproducibility.
    If seed is None, attempts to read from environment variable.
    """
    if seed is None:
        seed_str = os.environ.get(ENV_SEED)
        if seed_str:
            seed = int(seed_str)
        else:
            seed = 42 # Default seed if not specified
    
    logger.info(f"Setting global seed to {seed}")
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_seed() -> int:
    """Returns the current seed."""
    seed_str = os.environ.get(ENV_SEED, "42")
    return int(seed_str)

def get_imagenet_path() -> Optional[str]:
    """Returns the path to ImageNet if set, else None (will use streaming)."""
    path = os.environ.get(ENV_IMAGENET_PATH)
    if path:
        logger.info(f"Using ImageNet path from env: {path}")
        return path
    return None

def get_routing_cache_path() -> str:
    """Returns the path for routing cache."""
    # Default to project structure if not set
    default_path = "data/routing_cache"
    return _get_env_or_default(ENV_ROUTING_CACHE, default_path)

def get_results_path() -> str:
    """Returns the path for results."""
    default_path = "data/results"
    return _get_env_or_default(ENV_RESULTS, default_path)

def ensure_directories_exist():
    """Creates necessary directories if they don't exist."""
    paths = [
        get_routing_cache_path(),
        get_results_path(),
        "data/imagenet_trace",
        "data/imagenet_benchmark"
    ]
    for p in paths:
        Path(p).mkdir(parents=True, exist_ok=True)
        logger.debug(f"Ensured directory exists: {p}")

def get_config_summary() -> Dict[str, Any]:
    """Returns a summary of the current configuration."""
    return {
        "seed": get_seed(),
        "imagenet_path": get_imagenet_path(),
        "routing_cache": get_routing_cache_path(),
        "results": get_results_path()
    }
