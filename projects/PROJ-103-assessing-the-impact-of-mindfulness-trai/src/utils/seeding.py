"""
Seeding module for reproducible experiments.

Implements random seed pinning for numpy, random, and torch modules
to ensure deterministic output on re-run.

Seed value: 42 (per project reproducibility standards)
"""
import random
from typing import Optional, Union
import os

import numpy as np

# Attempt to import torch; handle gracefully if not installed
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False


DEFAULT_SEED = 42


def set_all_seeds(seed: Optional[int] = None) -> None:
    """
    Set random seeds for numpy, random, and torch (if available) to ensure
    reproducibility across runs.
    
    Args:
        seed: The seed value to use. Defaults to DEFAULT_SEED (42) if None.
    
    Side effects:
        - Sets numpy.random.seed
        - Sets random.seed
        - Sets torch.manual_seed, torch.cuda.manual_seed, torch.cuda.manual_seed_all
          (if torch is available)
        - Sets environment variables for deterministic behavior in torch (if available)
    
    Note:
        Full determinism in deep learning (especially with CuDNN) is not always
        guaranteed even with fixed seeds due to non-deterministic algorithms.
        This function sets common determinism flags where available.
    """
    if seed is None:
        seed = DEFAULT_SEED

    # Set numpy seed
    np.random.seed(seed)

    # Set random module seed
    random.seed(seed)

    # Set torch seeds if available
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
        
        # Set deterministic behavior flags for torch
        # Note: These may impact performance but improve reproducibility
        os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
        torch.use_deterministic_algorithms(True, warn_only=False)
        
        # Set CuDNN determinism
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False


def get_seed() -> int:
    """
    Get the default seed value used by this module.
    
    Returns:
        The default seed integer (42).
    """
    return DEFAULT_SEED


def verify_determinism(
    test_func, 
    iterations: int = 2, 
    *args, 
    **kwargs
) -> bool:
    """
    Verify that a function produces deterministic output when seeds are reset.
    
    Args:
        test_func: A callable that takes no arguments (or accepts *args, **kwargs)
                   and returns a numpy array, torch tensor, or comparable object.
        iterations: Number of times to run the verification (default 2).
        *args: Positional arguments to pass to test_func.
        **kwargs: Keyword arguments to pass to test_func.
    
    Returns:
        True if all iterations produce identical results, False otherwise.
    
    Raises:
        RuntimeError: If the results from different runs are not identical.
    """
    results = []
    for i in range(iterations):
        # Reset seeds before each run
        set_all_seeds(DEFAULT_SEED)
        result = test_func(*args, **kwargs)
        results.append(result)
    
    # Compare results
    for i in range(1, len(results)):
        if not _are_identical(results[0], results[i]):
            raise RuntimeError(
                f"Determinism verification failed: results {0} and {i} differ."
            )
    
    return True


def _are_identical(obj1, obj2) -> bool:
    """
    Check if two objects (numpy arrays, torch tensors, or others) are identical.
    
    Args:
        obj1: First object.
        obj2: Second object.
    
    Returns:
        True if objects are identical, False otherwise.
    """
    # Handle numpy arrays
    if isinstance(obj1, np.ndarray) and isinstance(obj2, np.ndarray):
        return np.array_equal(obj1, obj2)
    
    # Handle torch tensors
    if TORCH_AVAILABLE:
        if isinstance(obj1, torch.Tensor) and isinstance(obj2, torch.Tensor):
            return torch.equal(obj1, obj2)
    
    # Fallback to direct comparison for other types
    return obj1 == obj2
