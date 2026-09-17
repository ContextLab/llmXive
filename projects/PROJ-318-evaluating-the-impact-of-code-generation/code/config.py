"""
Configuration module for the research pipeline.
Handles random seed pinning, device configuration, and memory limits.
"""
import os
import logging
import random
import numpy as np
from typing import Optional, Dict, Any
import torch

# Constants
SEED = 42
MAX_METHODS = 1000  # Fixed sample size per Spec FR-001

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class ConfigException(Exception):
    """Custom exception for configuration errors."""
    pass

class Config:
    """Container for configuration values."""
    def __init__(self):
        self.seed = SEED
        self.max_methods = MAX_METHODS
        self.device = None
        self.dtype = None
        self.max_memory_mb = 7000  # 7 GB RAM limit

_config = None

def get_config() -> Config:
    """Returns the singleton configuration instance."""
    global _config
    if _config is None:
        _config = Config()
        set_global_seed(_config.seed)
    return _config

def set_global_seed(seed: int) -> None:
    """Sets the random seed for reproducibility."""
    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(seed)
    logger.info(f"Global seed set to {seed}")

def configure_logging(level: int = logging.INFO) -> None:
    """Configures the logging level."""
    logging.getLogger().setLevel(level)
    logger.setLevel(level)

def get_device_and_dtype() -> tuple:
    """
    Determines the best available device and data type.
    Returns:
        Tuple[torch.device, torch.dtype]
    """
    if torch.cuda.is_available():
        device = torch.device("cuda")
        dtype = torch.float16
    elif hasattr(torch.backends, 'mps') and torch.backends.mps.is_available():
        device = torch.device("mps")
        dtype = torch.float16
    else:
        device = torch.device("cpu")
        dtype = torch.float32
    
    return device, dtype

def get_quantization_config() -> Optional[Dict[str, Any]]:
    """
    Returns quantization configuration if applicable.
    Currently handled dynamically in model_loader, but this serves as a placeholder.
    """
    return None

def get_rate_limit_config() -> Dict[str, Any]:
    """Returns rate limiting configuration."""
    return {
        "requests_per_minute": 60,
        "retries": 3,
        "backoff_factor": 2.0
    }

def get_max_memory_mb() -> int:
    """Returns the maximum allowed memory in MB."""
    return get_config().max_memory_mb
