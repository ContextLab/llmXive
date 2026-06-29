"""
Deterministic seed handling utilities for reproducible research.

This module provides centralized seed management for all random operations
across the pipeline. It ensures reproducibility by setting seeds for:
- Python's random module
- NumPy random operations
- PyTorch (if available)

Usage:
    from src.utils.seed import set_seed, get_seed_parser
    import argparse
    
    parser = argparse.ArgumentParser()
    parser = get_seed_parser(parser)
    args = parser.parse_args()
    set_seed(args.seed)
"""

import argparse
import os
import random
import sys

import numpy as np

# Optional: PyTorch support
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Default seed value
DEFAULT_SEED = 42

# Global seed state
_current_seed = DEFAULT_SEED

def get_seed_parser(parser: argparse.ArgumentParser) -> argparse.ArgumentParser:
    """
    Add --seed argument to an existing argument parser.
    
    Args:
        parser: An existing argparse.ArgumentParser instance
        
    Returns:
        The same parser with --seed argument added
    """
    parser.add_argument(
        '--seed',
        type=int,
        default=DEFAULT_SEED,
        help=f'Deterministic random seed for reproducibility (default: {DEFAULT_SEED})'
    )
    return parser

def set_seed(seed: int) -> None:
    """
    Set random seeds for all supported libraries to ensure reproducibility.
    
    Args:
        seed: Integer seed value to use for random operations
    """
    global _current_seed
    _current_seed = seed
    
    # Set Python's random seed
    random.seed(seed)
    
    # Set NumPy random seed
    np.random.seed(seed)
    
    # Set PyTorch seeds if available
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    
    # Set environment variable for some libraries
    os.environ['PYTHONHASHSEED'] = str(seed)

def get_seed() -> int:
    """
    Get the currently set seed value.
    
    Returns:
        The current seed integer
    """
    return _current_seed

def get_rng_state() -> dict:
    """
    Get the current random number generator state for all libraries.
    
    Returns:
        Dictionary containing RNG states for reproducibility checkpointing
    """
    state = {
        'python_random': random.getstate(),
        'numpy': np.random.get_state(),
    }
    
    if TORCH_AVAILABLE:
        state['torch'] = {
            'cpu': torch.get_rng_state(),
        }
        if torch.cuda.is_available():
            state['torch']['cuda'] = torch.cuda.get_rng_state_all()
    
    return state

def set_rng_state(state: dict) -> None:
    """
    Restore RNG state from a checkpoint for exact reproducibility.
    
    Args:
        state: Dictionary containing RNG states from get_rng_state()
    """
    # Restore Python random state
    random.setstate(state['python_random'])
    
    # Restore NumPy state
    np.random.set_state(state['numpy'])
    
    # Restore PyTorch state if available
    if TORCH_AVAILABLE and 'torch' in state:
        torch.set_rng_state(state['torch']['cpu'])
        if 'cuda' in state['torch'] and torch.cuda.is_available():
            torch.cuda.set_rng_state_all(state['torch']['cuda'])

class SeedContext:
    """
    Context manager for temporary seed setting.
    
    Usage:
        with SeedContext(123):
            # Operations with seed 123
            pass
        # Seed restored to previous value
    """
    
    def __init__(self, seed: int):
        self.seed = seed
        self.previous_state = None
    
    def __enter__(self):
        self.previous_state = get_rng_state()
        set_seed(self.seed)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_state is not None:
            set_rng_state(self.previous_state)
        return False

def validate_seed(seed: int) -> bool:
    """
    Validate that a seed value is appropriate.
    
    Args:
        seed: Seed value to validate
        
    Returns:
        True if seed is valid, raises ValueError otherwise
    """
    if not isinstance(seed, int):
        raise ValueError(f"Seed must be an integer, got {type(seed).__name__}")
    if seed < 0:
        raise ValueError(f"Seed must be non-negative, got {seed}")
    if seed > 2**31 - 1:
        raise ValueError(f"Seed must fit in 32-bit integer, got {seed}")
    return True
