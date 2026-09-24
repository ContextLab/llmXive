import os
import random
import numpy as np
import torch
from typing import Optional, Dict, Any
from pathlib import Path

# Project root directory
PROJECT_ROOT = Path(__file__).resolve().parent.parent

# Directories
ROUTING_CACHE_DIR = PROJECT_ROOT / "data" / "routing_cache"
RESULTS_DIR = PROJECT_ROOT / "data" / "results"
DATA_DIR = PROJECT_ROOT / "data"

def ensure_directories_exist():
    """
    Ensure all necessary directories exist.
    """
    ROUTING_CACHE_DIR.mkdir(parents=True, exist_ok=True)
    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    DATA_DIR.mkdir(parents=True, exist_ok=True)

def get_seed() -> int:
    """
    Get random seed from environment variable or default.
    """
    return int(os.getenv("RANDOM_SEED", 42))

def set_seed(seed: int):
    """
    Set random seed for reproducibility.
    """
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)

def get_imagenet_path() -> Path:
    """
    Get path to ImageNet dataset (if local).
    """
    return Path(os.getenv("IMAGENET_PATH", ""))

def get_routing_cache_path() -> Path:
    """
    Get path to routing cache directory.
    """
    return ROUTING_CACHE_DIR

def get_results_path() -> Path:
    """
    Get path to results directory.
    """
    return RESULTS_DIR

def get_config_summary() -> Dict[str, Any]:
    """
    Get a summary of the current configuration.
    """
    return {
        "seed": get_seed(),
        "routing_cache_path": str(get_routing_cache_path()),
        "results_path": str(get_results_path()),
        "imagenet_path": str(get_imagenet_path())
    }
