"""
Deterministic Random Seed Management.

Ensures reproducibility by managing seeds for numpy, random, and torch (if available).
"""
import os
import random
from typing import Optional, Dict, Any
import numpy as np
import logging
from utils.logger import get_logger

logger = get_logger("seed_manager")

_current_seed = None
_state_cache = {}

def set_seed(seed: int):
    """Set global random seeds for reproducibility."""
    global _current_seed
    _current_seed = seed
    random.seed(seed)
    np.random.seed(seed)
    logger.debug(f"Seeds set to {seed}")

def get_seed() -> Optional[int]:
    return _current_seed

def reset_to_seed():
    """Reset to the previously set seed."""
    if _current_seed is not None:
        set_seed(_current_seed)

def get_state() -> Dict[str, Any]:
    """Get the current state of random generators."""
    return {
        "random": random.get_state(),
        "numpy": np.random.get_state(),
        "seed": _current_seed
    }

def set_state(state: Dict[str, Any]):
    """Restore the state of random generators."""
    random.set_state(state["random"])
    np.random.set_state(state["numpy"])
    global _current_seed
    _current_seed = state["seed"]
    logger.debug("Random state restored.")
