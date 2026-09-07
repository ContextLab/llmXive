"""
Deterministic random seed management utility.

This module provides functions to set and manage random seeds
for reproducible experiments across numpy, random, and os modules.
"""
import os
import random
from typing import Optional, Dict, Any
import numpy as np
import logging

logger = logging.getLogger(__name__)

# Global seed state
_current_seed: Optional[int] = None
_random_state: Optional[random.Random] = None
_np_state: Optional[np.random.RandomState] = None

def set_seed(seed: int) -> None:
    """
    Set random seeds for all relevant modules.
    
    Args:
        seed: Random seed value
    """
    global _current_seed, _random_state, _np_state
    
    _current_seed = seed
    random.seed(seed)
    np.random.seed(seed)
    os.environ['PYTHONHASHSEED'] = str(seed)
    
    # Initialize state objects
    _random_state = random.Random(seed)
    _np_state = np.random.RandomState(seed)
    
    logger.debug(f"Random seed set to: {seed}")

def get_seed() -> Optional[int]:
    """
    Get the current random seed.
    
    Returns:
        Current seed or None if not set
    """
    return _current_seed

def reset_to_seed() -> None:
    """Reset to the previously set seed, or use default if not set."""
    if _current_seed is not None:
        set_seed(_current_seed)
    else:
        # Default seed
        set_seed(42)

def get_state() -> Dict[str, Any]:
    """
    Get the current random state for checkpointing.
    
    Returns:
        Dictionary containing random states
    """
    return {
        "seed": _current_seed,
        "random_state": _random_state.getstate() if _random_state else None,
        "np_state": _np_state.get_state() if _np_state else None
    }

def set_state(state: Dict[str, Any]) -> None:
    """
    Restore a previously saved random state.
    
    Args:
        state: Dictionary containing random states
    """
    global _current_seed, _random_state, _np_state
    
    _current_seed = state.get("seed")
    
    if state.get("random_state") is not None:
        _random_state = random.Random()
        _random_state.setstate(state["random_state"])
        random.setstate(_random_state.getstate())
    
    if state.get("np_state") is not None:
        _np_state = np.random.RandomState()
        _np_state.set_state(state["np_state"])
        np.random.set_state(_np_state.get_state())
    
    logger.debug("Random state restored from checkpoint")
