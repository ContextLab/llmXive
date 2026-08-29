"""
Deterministic seed handling module for the llmXive perovskite pipeline.

This module provides a centralized utility to handle random seed initialization
across all modules (ingest, cleaning, descriptors, analysis) to ensure
reproducible results.

Usage:
    from src.utils.seed_manager import init_seed
    init_seed(42)
"""
import random
import os
import sys
from typing import Optional
import numpy as np

# Try to import torch if available, but don't fail if not
try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

# Try to import tensorflow if available, but don't fail if not
try:
    import tensorflow as tf
    HAS_TENSORFLOW = True
except ImportError:
    HAS_TENSORFLOW = False

# Try to import pandas if available
try:
    import pandas as pd
    HAS_PANDAS = True
except ImportError:
    HAS_PANDAS = False

# Global seed state
_seed_initialized = False
_current_seed = None


def init_seed(seed: int = 42) -> None:
    """
    Initialize all random number generators with the given seed.
    
    This function sets the seed for:
    - Python's built-in random module
    - NumPy
    - PyTorch (if available)
    - TensorFlow (if available)
    - Environment variable for reproducibility
    
    Args:
        seed: The random seed to use. Default is 42.
    
    Raises:
        ValueError: If seed is not a non-negative integer.
    """
    global _seed_initialized, _current_seed
    
    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got {seed}")
    
    _current_seed = seed
    _seed_initialized = True
    
    # Set Python's random seed
    random.seed(seed)
    
    # Set NumPy's random seed
    np.random.seed(seed)
    
    # Set PyTorch's random seed if available
    if HAS_TORCH:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)  # if you are using multi-GPU
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    
    # Set TensorFlow's random seed if available
    if HAS_TENSORFLOW:
        tf.random.set_seed(seed)
    
    # Set environment variable for reproducibility
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # Log the initialization
    logger = setup_logger_module()
    logger.info(f"Random seed initialized to {seed}")


def get_seed() -> Optional[int]:
    """
    Get the currently initialized seed.
    
    Returns:
        The current seed value, or None if not initialized.
    """
    return _current_seed


def is_seed_initialized() -> bool:
    """
    Check if the seed has been initialized.
    
    Returns:
        True if seed is initialized, False otherwise.
    """
    return _seed_initialized


def setup_logger_module():
    """
    Setup a logger for this module.
    
    Returns:
        A configured logger instance.
    """
    import logging
    logger = logging.getLogger(__name__)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
        logger.setLevel(logging.INFO)
    return logger


# Example usage for command-line argument parsing
def add_seed_argument(parser):
    """
    Add a --seed argument to an argparse parser.
    
    Args:
        parser: An argparse.ArgumentParser instance.
    
    Returns:
        The modified parser.
    """
    import argparse
    if not isinstance(parser, argparse.ArgumentParser):
        raise TypeError("parser must be an argparse.ArgumentParser instance")
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    return parser
