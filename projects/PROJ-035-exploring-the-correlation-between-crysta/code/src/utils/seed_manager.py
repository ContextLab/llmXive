"""
Seed management utilities for deterministic execution across the pipeline.
Provides centralized random state handling for numpy, random, and torch (if available).
"""
import random
import os
import sys
from typing import Optional
import numpy as np
import argparse
import logging

# Global seed state
_seed_initialized = False
_current_seed = 42  # Default seed as per requirement

def setup_logger_module(name: str = "seed_manager", level: int = logging.INFO) -> logging.Logger:
    """
    Setup a module-specific logger.

    Args:
        name: Logger name (usually __name__)
        level: Logging level

    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(level)
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stdout)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        handler.setFormatter(formatter)
        logger.addHandler(handler)
    return logger

def init_seed(seed: int = 42) -> None:
    """
    Initialize all random seeds for deterministic execution.

    This function sets seeds for:
    - Python's random module
    - NumPy's random number generator
    - Environment variable PYTHONHASHSEED

    Args:
        seed: Integer seed value (default: 42)
    """
    global _seed_initialized, _current_seed

    if seed is None:
        seed = 42

    _current_seed = seed
    _seed_initialized = True

    # Set Python random seed
    random.seed(seed)

    # Set NumPy random seed
    np.random.seed(seed)

    # Set environment variable for hash randomization
    os.environ['PYTHONHASHSEED'] = str(seed)

    # Attempt to set torch seed if available (optional, non-fatal)
    try:
        import torch
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    except ImportError:
        pass  # Torch not installed, which is fine

def get_seed() -> int:
    """
    Get the currently initialized seed value.

    Returns:
        Current seed value, or 42 if not initialized.
    """
    return _current_seed if _seed_initialized else 42

def is_seed_initialized() -> bool:
    """
    Check if the seed has been initialized.

    Returns:
        True if init_seed() has been called, False otherwise.
    """
    return _seed_initialized

def add_seed_argument(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add a --seed argument to an argparse.ArgumentParser.

    Args:
        parser: The argument parser to extend

    Returns:
        The same parser with the added argument
    """
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for deterministic execution (default: 42)'
    )
    return parser

def validate_seed(seed: int) -> bool:
    """
    Validate that a seed value is a non-negative integer.

    Args:
        seed: The seed value to validate

    Returns:
        True if valid, False otherwise
    """
    return isinstance(seed, int) and seed >= 0

def reset_seed() -> None:
    """
    Reset the seed state to uninitialized.
    Useful for testing scenarios where re-initialization is needed.
    """
    global _seed_initialized, _current_seed
    _seed_initialized = False
    _current_seed = 42
