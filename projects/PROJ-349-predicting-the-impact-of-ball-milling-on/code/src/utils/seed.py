"""
Seed management utility for the llmXive ball milling prediction pipeline.

This module provides a centralized way to pin all random states across
the entire project to ensure reproducibility of experiments and models.
"""

import os
import random
from typing import Optional, Dict, Any

import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

# Default seed value - can be overridden via environment variable
DEFAULT_SEED = 42
SEED_ENV_VAR = "BALL_MILLING_SEED"

# Global seed state
_global_seed: Optional[int] = None
_seed_config: Dict[str, Any] = {}


def get_seed() -> int:
    """
    Retrieve the global seed value.
    
    Checks in order:
    1. Environment variable BALL_MILLING_SEED
    2. Previously set global seed
    3. Default seed (42)
    
    Returns:
        int: The seed value to use for random operations.
    """
    # Check environment variable first
    env_seed = os.environ.get(SEED_ENV_VAR)
    if env_seed is not None:
        try:
            return int(env_seed)
        except ValueError:
            raise ValueError(f"Invalid seed value in {SEED_ENV_VAR}: {env_seed}. Must be an integer.")
    
    # Return global seed if set
    if _global_seed is not None:
        return _global_seed
    
    # Return default
    return DEFAULT_SEED


def set_seed(seed: Optional[int] = None) -> int:
    """
    Set the global seed and propagate to all random number generators.
    
    Args:
        seed: Optional seed value. If None, uses environment variable or default.
    
    Returns:
        int: The seed value that was set.
    
    Raises:
        ValueError: If the seed value is not a non-negative integer.
    """
    if seed is None:
        seed = get_seed()
    
    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got: {seed}")
    
    global _global_seed
    _global_seed = seed
    
    # Propagate to all libraries
    _propagate_seed(seed)
    
    return seed


def _propagate_seed(seed: int) -> None:
    """
    Propagate the seed to all random number generators used in the project.
    
    Args:
        seed: The seed value to set.
    """
    # Python's random module
    random.seed(seed)
    
    # NumPy
    np.random.seed(seed)
    
    # PyTorch (if available)
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    
    # Store configuration for reference
    _seed_config['seed'] = seed
    _seed_config['torch_available'] = TORCH_AVAILABLE
    _seed_config['cuda_available'] = TORCH_AVAILABLE and torch.cuda.is_available() if TORCH_AVAILABLE else False


def get_random_state() -> Dict[str, Any]:
    """
    Get the current state of all random number generators.
    
    Returns:
        Dict containing the state of each random generator.
    """
    state = {
        'python_random': random.getstate(),
        'numpy_random': np.random.get_state(),
    }
    
    if TORCH_AVAILABLE:
        state['torch_cpu'] = torch.get_rng_state()
        if torch.cuda.is_available():
            state['torch_cuda'] = torch.cuda.get_rng_state_all()
    
    return state


def set_random_state(state: Dict[str, Any]) -> None:
    """
    Restore the state of all random number generators.
    
    Args:
        state: Dictionary containing states from get_random_state().
    """
    random.setstate(state['python_random'])
    np.random.set_state(state['numpy_random'])
    
    if TORCH_AVAILABLE and 'torch_cpu' in state:
        torch.set_rng_state(state['torch_cpu'])
        if 'torch_cuda' in state and torch.cuda.is_available():
            torch.cuda.set_rng_state_all(state['torch_cuda'])


def get_seed_config() -> Dict[str, Any]:
    """
    Get the current seed configuration.
    
    Returns:
        Dict with seed value and availability flags.
    """
    return _seed_config.copy()


def init_seed(seed: Optional[int] = None) -> int:
    """
    Initialize the seed for the entire pipeline.
    
    This should be called at the very beginning of the main entry point
    to ensure all subsequent random operations are reproducible.
    
    Args:
        seed: Optional seed value. If None, uses environment variable or default.
    
    Returns:
        int: The seed value that was initialized.
    
    Example:
        >>> from src.utils.seed import init_seed
        >>> seed = init_seed()  # Uses env var or default 42
        >>> # Now all random operations are reproducible
    """
    return set_seed(seed)