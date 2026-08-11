"""
Deterministic random seed management module.

Implements a singleton pattern for reproducible randomness across the project,
ensuring Constitution Principle I (Reproducibility) and FR-008 (Statistical Variance).
"""
import random
import os
from typing import Optional, Dict, Any, Generator
from pathlib import Path
import numpy as np
from utils.logging import get_logger, info, debug

# Global state for singleton pattern
_global_seed: Optional[int] = None
_is_deterministic: bool = False
_logger = get_logger(__name__)

def set_global_seed(seed: Optional[int] = None, deterministic: bool = False) -> int:
    """
    Sets the global random seed for Python, NumPy, and (if available) PyTorch.
    If seed is None, generates one based on system time or environment variable.
    
    Args:
        seed: The seed value to use. If None, uses environment variable or defaults to 42.
        deterministic: If True, enables deterministic behavior for PyTorch (if available).
    
    Returns:
        The seed value that was set.
    """
    global _global_seed, _is_deterministic

    if seed is None:
        seed = int(os.environ.get("LLMXIVE_SEED", "42"))

    _global_seed = seed
    _is_deterministic = deterministic

    # Set Python random seed
    random.seed(seed)

    # Set NumPy seed
    np.random.seed(seed)

    # Set PyTorch seed if available (optional dependency)
    try:
        import torch
        torch.manual_seed(seed)
        if deterministic:
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
            os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"
        debug("PyTorch seed set.")
    except ImportError:
        debug("PyTorch not installed; skipping torch seed.")

    info(f"Global seed set to {seed} (deterministic={deterministic})")
    return seed

def get_global_seed() -> Optional[int]:
    """Returns the currently set global seed."""
    return _global_seed

def is_deterministic() -> bool:
    """Returns whether the current run is in deterministic mode."""
    return _is_deterministic

def generate_seed() -> int:
    """Generates a new random seed based on current time."""
    import time
    return int(time.time() * 1000) % (2**32)

def ensure_seed_set() -> int:
    """Ensures a global seed is set; if not, generates and sets one."""
    if _global_seed is None:
        new_seed = generate_seed()
        set_global_seed(new_seed)
    return _global_seed

def get_rng(seed: Optional[int] = None) -> np.random.Generator:
    """
    Returns a NEW NumPy random Generator instance seeded with the provided seed
    or the global seed. This allows for isolated randomness per function call
    while maintaining reproducibility.
    
    This implements the singleton pattern for seed management:
    - If a specific seed is provided, it uses that.
    - If no seed is provided, it falls back to the global seed.
    - If no global seed is set, it generates a new one (but logs a warning).
    
    Args:
        seed: Optional specific seed for this generator. If None, uses global seed.
    
    Returns:
        A fresh np.random.Generator instance.
    
    Note:
        Returns a new Generator instance each time, not a singleton generator.
        The 'singleton' aspect refers to the seed management, not the generator object itself.
        This design ensures that multiple calls with the same seed produce identical sequences,
        while different calls can have independent random streams if needed.
    """
    if seed is None:
        seed = _global_seed
    
    if seed is None:
        # If no global seed is set, generate one but warn
        _logger.warning("No global seed set. Generating a temporary seed. "
                      "For reproducibility, call set_global_seed() first.")
        seed = generate_seed()
    
    rng = np.random.default_rng(seed)
    return rng

def reset_to_global_seed() -> None:
    """Resets all random states to the global seed."""
    if _global_seed is not None:
        set_global_seed(_global_seed, _is_deterministic)

class SeedContext:
    """
    Context manager to temporarily set a seed, then restore the previous state.
    Useful for unit tests or specific stochastic operations.
    """
    def __init__(self, seed: Optional[int] = None):
        self.seed = seed
        self.prev_seed = _global_seed
        self.prev_deterministic = _is_deterministic

    def __enter__(self):
        if self.seed is not None:
            set_global_seed(self.seed)
        else:
            set_global_seed(generate_seed())
        return _global_seed

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.prev_seed is not None:
            set_global_seed(self.prev_seed, self.prev_deterministic)
        else:
            reset_to_global_seed()
        return False