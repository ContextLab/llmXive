"""
Deterministic seed setting utility for reproducibility across batches.

This module provides functions to set random seeds for Python's random module,
NumPy, and PyTorch to ensure reproducible results across runs.
"""

import random
import os
import torch
import numpy as np
from typing import Optional, Dict, Any
from pathlib import Path

# Default seed value
DEFAULT_SEED = 42

# Global seed configuration storage
_seed_config: Dict[str, Any] = {
    "seed": DEFAULT_SEED,
    "cudnn_deterministic": True,
    "cudnn_benchmark": False,
    "torch_manual_seed": True,
    "numpy_seed": True,
    "random_seed": True,
    "python_hash_seed": True
}

def set_deterministic_seed(seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Set deterministic seeds for all random number generators.
    
    Args:
        seed: The seed value to use. If None, uses DEFAULT_SEED.
    
    Returns:
        Dict containing the seed configuration that was applied.
    
    Raises:
        RuntimeError: If setting seeds fails for any reason.
    """
    if seed is None:
        seed = DEFAULT_SEED
    
    try:
        # Set Python's random seed
        random.seed(seed)
        _seed_config["random_seed"] = True
    
        # Set NumPy seed
        np.random.seed(seed)
        _seed_config["numpy_seed"] = True
    
        # Set PyTorch seeds
        torch.manual_seed(seed)
        _seed_config["torch_manual_seed"] = True
    
        # Set CUDA seeds if available (even in CPU mode, for consistency)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
        else:
            # Explicitly set CUDA seeds to None to indicate not available
            pass
    
        # Set environment variable for hash seed (Python 3.3+)
        if _seed_config["python_hash_seed"]:
            os.environ['PYTHONHASHSEED'] = str(seed)
    
        # Configure CuDNN for deterministic behavior
        # Note: These only have effect if CUDA is available
        torch.backends.cudnn.deterministic = _seed_config["cudnn_deterministic"]
        torch.backends.cudnn.benchmark = _seed_config["cudnn_benchmark"]
    
        # Set additional PyTorch reproducibility flags
        torch.use_deterministic_algorithms(True, warn_only=True)
    
        _seed_config["seed"] = seed
    
        return _seed_config.copy()
    
    except Exception as e:
        raise RuntimeError(f"Failed to set deterministic seed: {e}")

def get_seed_config() -> Dict[str, Any]:
    """
    Get the current seed configuration.
    
    Returns:
        Copy of the current seed configuration dictionary.
    """
    return _seed_config.copy()

def verify_reproducibility(seed: Optional[int] = None, n_runs: int = 3) -> bool:
    """
    Verify that setting the seed produces reproducible results.
    
    This function runs a simple test multiple times to verify that
    the seed setting produces identical results.
    
    Args:
        seed: The seed to test. If None, uses DEFAULT_SEED.
        n_runs: Number of times to run the test.
    
    Returns:
        True if results are reproducible across all runs.
    
    Raises:
        RuntimeError: If reproducibility verification fails.
    """
    if seed is None:
        seed = DEFAULT_SEED
    
    results = []
    
    for i in range(n_runs):
        # Set the seed
        set_deterministic_seed(seed)
        
        # Generate test values from each library
        test_random = random.random()
        test_numpy = np.random.random()
        test_torch = torch.rand(1).item()
        
        results.append({
            "random": test_random,
            "numpy": test_numpy,
            "torch": test_torch
        })
    
    # Check if all results are identical
    first_result = results[0]
    for i, result in enumerate(results[1:], 1):
        if (abs(result["random"] - first_result["random"]) > 1e-10 or
            abs(result["numpy"] - first_result["numpy"]) > 1e-10 or
            abs(result["torch"] - first_result["torch"]) > 1e-10):
            raise RuntimeError(
                f"Reproducibility verification failed on run {i}: "
                f"Results differ from first run."
            )
    
    return True

class DeterministicContext:
    """
    Context manager for temporary deterministic seeding.
    
    Allows temporarily setting a seed for a block of code,
    then restoring the previous state.
    
    Example:
        with DeterministicContext(seed=123):
            # Code that needs deterministic behavior
            pass
        # Original seed state is restored here
    """
    
    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the context manager.
        
        Args:
            seed: The seed to use within the context. If None, uses DEFAULT_SEED.
        """
        self.seed = seed if seed is not None else DEFAULT_SEED
        self.previous_config = None
    
    def __enter__(self):
        """Save current config and set new seed."""
        self.previous_config = get_seed_config().copy()
        set_deterministic_seed(self.seed)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore previous configuration."""
        # Restore the previous configuration
        if self.previous_config:
            # We need to manually restore since we don't have a setter
            # This is a simplified restoration
            if "seed" in self.previous_config:
                set_deterministic_seed(self.previous_config["seed"])
        return False

def main():
    """Main function for standalone execution and testing."""
    print("Testing deterministic seed setting...")
    
    # Test basic seed setting
    config = set_deterministic_seed(12345)
    print(f"Seed configuration: {config}")
    
    # Test reproducibility
    try:
        is_reproducible = verify_reproducibility(seed=12345, n_runs=5)
        print(f"Reproducibility verification: {'PASSED' if is_reproducible else 'FAILED'}")
    except RuntimeError as e:
        print(f"Reproducibility verification failed: {e}")
    
    # Test context manager
    with DeterministicContext(seed=99999):
        print(f"Inside context - seed: {get_seed_config()['seed']}")
        val1 = random.random()
    
    print(f"After context - seed: {get_seed_config()['seed']}")
    
    # Verify context manager restored state
    if get_seed_config()['seed'] == 12345:
        print("Context manager correctly restored previous seed state")
    else:
        print("Warning: Context manager did not restore previous seed state")
    
    print("Seed utility tests completed.")

if __name__ == "__main__":
    main()
