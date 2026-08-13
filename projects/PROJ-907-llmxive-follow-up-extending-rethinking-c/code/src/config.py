import os
import random
import numpy as np
import torch
from typing import Optional, Dict, Any
from pathlib import Path
import logging

logger = logging.getLogger(__name__)

# Project root is two levels up from code/src
PROJECT_ROOT = Path(__file__).parent.parent.parent
CODE_DIR = PROJECT_ROOT / "code"
DATA_DIR = CODE_DIR / "data"
RESULTS_DIR = DATA_DIR / "results"
ROUTING_CACHE_DIR = DATA_DIR / "routing_cache"

def set_seed(seed: Optional[int] = None):
    """Set random seeds for reproducibility."""
    if seed is None:
        seed = int(os.getenv('RANDOM_SEED', '42'))
    
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    
    logger.info(f"Random seed set to {seed}")

def get_seed() -> int:
    """Get the current random seed."""
    return int(os.getenv('RANDOM_SEED', '42'))

def get_imagenet_path() -> Path:
    """Get path to ImageNet dataset (not used in streaming mode)."""
    # In streaming mode, we don't need a local path
    return DATA_DIR / "imagenet"

def get_routing_cache_path() -> Path:
    """Get path to routing cache directory."""
    return ROUTING_CACHE_DIR

def get_results_path() -> Path:
    """Get path to results directory."""
    return RESULTS_DIR

def ensure_directories_exist():
    """Ensure all necessary directories exist."""
    directories = [
        CODE_DIR / "src",
        CODE_DIR / "tests",
        DATA_DIR,
        RESULTS_DIR,
        ROUTING_CACHE_DIR,
        DATA_DIR / "imagenet_trace",
        DATA_DIR / "imagenet_benchmark",
        DATA_DIR / "routing_cache",
        DATA_DIR / "results",
        PROJECT_ROOT / "docs"
    ]
    for dir_path in directories:
        dir_path.mkdir(parents=True, exist_ok=True)
    logger.info("Directories ensured.")

def get_config_summary() -> Dict[str, Any]:
    """Get a summary of the current configuration."""
    return {
        "seed": get_seed(),
        "trace_set_size": int(os.getenv('TRACE_SET_SIZE', '100')),
        "benchmark_set_start": int(os.getenv('BENCHMARK_SET_START', '100')),
        "project_root": str(PROJECT_ROOT),
        "data_dir": str(DATA_DIR),
        "results_dir": str(RESULTS_DIR),
        "routing_cache_dir": str(ROUTING_CACHE_DIR)
    }

# Initialize directories on module import
ensure_directories_exist()
