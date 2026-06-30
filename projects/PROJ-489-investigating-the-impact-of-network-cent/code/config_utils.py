"""
Environment configuration management for the Network Centrality and Sleep Synchrony Analysis pipeline.

This module provides utilities for setting up the environment reproducibility,
specifically handling random seed pinning as defined in config.yaml.
"""
import os
import random
from pathlib import Path
from typing import Any, Dict, Optional

import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Load configuration from a YAML file.
    
    Args:
        config_path: Path to the config file. Defaults to 'code/config.yaml'.
        
    Returns:
        Dictionary containing configuration parameters.
    """
    import yaml
    
    if config_path is None:
        config_path = Path(__file__).parent / "config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
    
    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def set_random_seed(config: Dict[str, Any], seed_key: str = "random_seed") -> None:
    """
    Set random seeds for reproducibility across Python, NumPy, and PyTorch.
    
    Reads the seed value from the configuration dictionary and applies it
    to all relevant random number generators.
    
    Args:
        config: Configuration dictionary loaded from YAML.
        seed_key: Key in the config dict where the seed value is stored.
    """
    if seed_key not in config:
        raise ValueError(f"Seed key '{seed_key}' not found in configuration.")
    
    seed = int(config[seed_key])
    
    # Set Python's random seed
    random.seed(seed)
    
    # Set NumPy's random seed
    np.random.seed(seed)
    
    # Set PyTorch's random seed if available
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    
    # Set environment variables for deterministic behavior (optional but recommended)
    os.environ['PYTHONHASHSEED'] = str(seed)


def setup_environment(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """
    Full environment setup: load config and initialize random seeds.
    
    Args:
        config_path: Optional path to config file.
        
    Returns:
        The loaded configuration dictionary.
    """
    config = load_config(config_path)
    set_random_seed(config)
    return config