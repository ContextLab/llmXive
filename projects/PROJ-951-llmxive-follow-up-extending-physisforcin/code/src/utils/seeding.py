"""
Deterministic seed setting utility for reproducibility across batches.

This module provides utilities to set and manage random seeds for Python's random,
NumPy, and PyTorch to ensure reproducible results across runs.
"""
import random
import os
import torch
import numpy as np
from typing import Optional, Dict, Any
from pathlib import Path
import logging
from contextlib import contextmanager

# Configure logging
logger = logging.getLogger(__name__)


def set_deterministic_seed(seed: int = 42, deterministic: bool = True, benchmark: bool = False) -> Dict[str, int]:
    """
    Set random seeds for all relevant libraries to ensure reproducibility.
    
    Args:
        seed: The random seed to use. Default is 42.
        deterministic: If True, use deterministic algorithms in PyTorch.
                       Note: This may impact performance.
        benchmark: If True and deterministic is False, use benchmark mode in PyTorch.
                    This can improve performance for models with fixed input sizes.
    
    Returns:
        Dict containing the seed configuration used.
    
    Raises:
        ValueError: If seed is not a non-negative integer.
    """
    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got {seed}")
    
    # Set Python random seed
    random.seed(seed)
    
    # Set NumPy seed
    np.random.seed(seed)
    
    # Set PyTorch seeds
    torch.manual_seed(seed)
    
    # Set CUDA seeds if available
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
    
    # Configure deterministic behavior
    if torch.cuda.is_available():
        torch.backends.cudnn.deterministic = deterministic
        torch.backends.cudnn.benchmark = benchmark and not deterministic
    
    # Set environment variable for deterministic operations
    if deterministic:
        os.environ['CUBLAS_WORKSPACE_CONFIG'] = ':4096:8'
        os.environ['PYTHONHASHSEED'] = str(seed)
    
    config = {
        'seed': seed,
        'deterministic': deterministic,
        'benchmark': benchmark,
        'python_random': random.getstate()[1][0],  # Current state marker
        'numpy_seed': np.random.get_state()[1][0],  # Current state marker
        'torch_seed': torch.initial_seed() & 0xffffffff  # Current state marker (truncated to 32-bit)
    }
    
    logger.info(f"Set deterministic seed: {seed} (deterministic={deterministic}, benchmark={benchmark})")
    
    return config


def get_seed_config(seed: int = 42) -> Dict[str, Any]:
    """
    Get the current seed configuration without modifying state.
    
    Args:
        seed: The seed value to report (does not set it).
    
    Returns:
        Dict with seed configuration details.
    """
    return {
        'seed': seed,
        'python_random_state': random.getstate()[1][0],
        'numpy_random_state': np.random.get_state()[1][0],
        'torch_initial_seed': torch.initial_seed() & 0xffffffff
    }


def verify_reproducibility(seed: int = 42, iterations: int = 3, tolerance: float = 1e-6) -> bool:
    """
    Verify that setting the seed produces reproducible results.
    
    This function runs a simple operation multiple times with the same seed
    and verifies the results are identical.
    
    Args:
        seed: The seed to test.
        iterations: Number of iterations to run.
        tolerance: Tolerance for floating point comparison.
    
    Returns:
        True if results are reproducible within tolerance, False otherwise.
    
    Raises:
        RuntimeError: If reproducibility fails.
    """
    results = []
    
    for i in range(iterations):
        # Reset seed
        set_deterministic_seed(seed)
        
        # Generate test data
        test_tensor = torch.randn(100, 100)
        test_array = np.random.randn(100, 100)
        test_random = [random.random() for _ in range(100)]
        
        # Compute a simple metric
        tensor_sum = test_tensor.sum().item()
        array_sum = test_array.sum().item()
        random_sum = sum(test_random)
        
        results.append({
            'tensor_sum': tensor_sum,
            'array_sum': array_sum,
            'random_sum': random_sum
        })
    
    # Compare all results
    first_result = results[0]
    for i, result in enumerate(results[1:], 1):
        if abs(result['tensor_sum'] - first_result['tensor_sum']) > tolerance:
            logger.error(f"Tensor sum mismatch at iteration {i}: {result['tensor_sum']} vs {first_result['tensor_sum']}")
            return False
        
        if abs(result['array_sum'] - first_result['array_sum']) > tolerance:
            logger.error(f"Array sum mismatch at iteration {i}: {result['array_sum']} vs {first_result['array_sum']}")
            return False
        
        if abs(result['random_sum'] - first_result['random_sum']) > tolerance:
            logger.error(f"Random sum mismatch at iteration {i}: {result['random_sum']} vs {first_result['random_sum']}")
            return False
    
    logger.info(f"Reproducibility verified for seed {seed} over {iterations} iterations")
    return True


class DeterministicContext:
    """
    Context manager for temporary deterministic execution.
    
    This context manager allows running code with a specific seed and
    automatically restores the previous state upon exit.
    """
    
    def __init__(self, seed: int = 42, deterministic: bool = True):
        self.seed = seed
        self.deterministic = deterministic
        self._previous_state = None
    
    def __enter__(self):
        # Save current state
        self._previous_state = {
            'random': random.getstate(),
            'numpy': np.random.get_state(),
            'torch': torch.initial_seed()
        }
        
        # Set new seed
        set_deterministic_seed(self.seed, self.deterministic)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore previous state
        if self._previous_state:
            random.setstate(self._previous_state['random'])
            np.random.set_state(self._previous_state['numpy'])
            # Note: torch.random.set_initial_seed() is not available in all versions
            # We rely on re-seeding if needed
        return False


def main():
    """
    Main function for testing the seeding module.
    """
    print("Testing deterministic seeding...")
    
    # Test basic seed setting
    config = set_deterministic_seed(12345)
    print(f"Seed config: {config}")
    
    # Test reproducibility
    is_reproducible = verify_reproducibility(12345)
    print(f"Reproducibility test: {'PASSED' if is_reproducible else 'FAILED'}")
    
    # Test context manager
    with DeterministicContext(54321):
        tensor1 = torch.randn(10)
        array1 = np.random.randn(10)
    
    with DeterministicContext(54321):
        tensor2 = torch.randn(10)
        array2 = np.random.randn(10)
    
    print(f"Tensor equality: {torch.allclose(tensor1, tensor2)}")
    print(f"Array equality: {np.allclose(array1, array2)}")
    
    # Test get_seed_config
    seed_config = get_seed_config(999)
    print(f"Seed config (no change): {seed_config}")


if __name__ == "__main__":
    main()
