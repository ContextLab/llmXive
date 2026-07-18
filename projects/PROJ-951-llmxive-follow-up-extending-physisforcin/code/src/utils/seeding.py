"""
Deterministic seed setting utility for reproducibility across batches.

This module provides functions to set and manage random seeds for Python's
random module, NumPy, and PyTorch to ensure reproducible results across runs.
"""
import random
import os
import torch
import numpy as np
from typing import Optional, Dict, Any
from pathlib import Path
import logging

# Configure logging
logger = logging.getLogger(__name__)

# Default seed value if none provided
DEFAULT_SEED = 42


def set_deterministic_seed(seed: Optional[int] = None) -> int:
    """
    Set random seeds for all relevant libraries to ensure deterministic behavior.

    Args:
        seed: Random seed to use. If None, uses DEFAULT_SEED.

    Returns:
        The seed value that was set.
    """
    if seed is None:
        seed = DEFAULT_SEED

    # Set seed for Python's random module
    random.seed(seed)

    # Set seed for NumPy
    np.random.seed(seed)

    # Set seed for PyTorch
    torch.manual_seed(seed)

    # Set seed for PyTorch CUDA (if available, though we're CPU-only)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)

    # Set environment variables for deterministic behavior
    os.environ['PYTHONHASHSEED'] = str(seed)

    # Set PyTorch deterministic flags
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    logger.info(f"Set deterministic seed to {seed}")

    return seed


def get_seed_config(seed: Optional[int] = None) -> Dict[str, Any]:
    """
    Get a configuration dictionary for the current seed settings.

    Args:
        seed: Random seed to use. If None, uses DEFAULT_SEED.

    Returns:
        Dictionary containing seed configuration.
    """
    if seed is None:
        seed = DEFAULT_SEED

    return {
        "seed": seed,
        "python_random": random.getstate()[1][0],  # Current state indicator
        "numpy_seed": np.random.get_state()[1][0],  # Current state indicator
        "torch_seed": torch.initial_seed() if hasattr(torch, 'initial_seed') else None,
        "cudnn_deterministic": torch.backends.cudnn.deterministic,
        "cudnn_benchmark": torch.backends.cudnn.benchmark,
        "python_hash_seed": os.environ.get('PYTHONHASHSEED', 'not set')
    }


def verify_reproducibility(seed: Optional[int] = None, num_iterations: int = 3) -> bool:
    """
    Verify that setting the seed produces reproducible results.

    This function performs a simple test by generating random numbers
    after setting the seed multiple times and checking if they match.

    Args:
        seed: Random seed to use. If None, uses DEFAULT_SEED.
        num_iterations: Number of times to test reproducibility.

    Returns:
        True if results are reproducible, False otherwise.
    """
    if seed is None:
        seed = DEFAULT_SEED

    test_results = []

    for i in range(num_iterations):
        # Set the seed
        set_deterministic_seed(seed)

        # Generate some random values
        py_random_val = random.random()
        np_random_val = np.random.random()
        torch_random_val = torch.rand(1).item()

        test_results.append({
            "iteration": i,
            "python_random": py_random_val,
            "numpy_random": np_random_val,
            "torch_random": torch_random_val
        })

        if i > 0:
            # Compare with previous iteration
            prev = test_results[i - 1]
            if (py_random_val != prev["python_random"] or
                np_random_val != prev["numpy_random"] or
                torch_random_val != prev["torch_random"]):
                logger.error(f"Reproducibility failed at iteration {i}")
                return False

    logger.info("Reproducibility verified successfully")
    return True


class DeterministicContext:
    """
    Context manager for temporarily setting a deterministic seed.

    This context manager sets the seed on entry and restores the previous
    state on exit, allowing for controlled reproducible sections of code.

    Example:
        with DeterministicContext(42):
            # Code that needs to be deterministic
            result = some_function()
        # Seed is restored to previous state
    """

    def __init__(self, seed: Optional[int] = None):
        """
        Initialize the context manager.

        Args:
            seed: Random seed to use. If None, uses DEFAULT_SEED.
        """
        self.seed = seed if seed is not None else DEFAULT_SEED
        self.previous_state = None

    def __enter__(self):
        """Save current state and set the new seed."""
        # Save current states
        self.previous_state = {
            "python_random": random.getstate(),
            "numpy_random": np.random.get_state(),
            "torch_seed": torch.initial_seed() if hasattr(torch, 'initial_seed') else None
        }

        # Set new seed
        set_deterministic_seed(self.seed)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Restore previous state."""
        if self.previous_state:
            random.setstate(self.previous_state["python_random"])
            np.random.set_state(self.previous_state["numpy_random"])
            # Note: PyTorch seed restoration is not directly supported
            # but the deterministic flags remain set
        return False


def main():
    """
    Main function to demonstrate seeding functionality.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Deterministic seed utility")
    parser.add_argument("--seed", type=int, default=DEFAULT_SEED,
                      help=f"Random seed to use (default: {DEFAULT_SEED})")
    parser.add_argument("--verify", action="store_true",
                      help="Verify reproducibility")
    parser.add_argument("--config", action="store_true",
                      help="Print seed configuration")

    args = parser.parse_args()

    # Set up logging
    logging.basicConfig(level=logging.INFO)

    logger.info("=== Deterministic Seed Utility ===")

    # Set the seed
    set_deterministic_seed(args.seed)

    if args.config:
        config = get_seed_config(args.seed)
        logger.info(f"Seed configuration: {config}")

    if args.verify:
        success = verify_reproducibility(args.seed)
        if success:
            logger.info("Verification passed")
        else:
            logger.error("Verification failed")

    # Demonstrate reproducibility
    logger.info("\nDemonstrating reproducibility:")
    for i in range(3):
        set_deterministic_seed(args.seed)
        val = random.random()
        logger.info(f"Iteration {i}: random.random() = {val}")

    # Demonstrate context manager
    logger.info("\nDemonstrating context manager:")
    with DeterministicContext(args.seed):
        val1 = random.random()
        logger.info(f"Inside context: random.random() = {val1}")

    val2 = random.random()
    logger.info(f"After context: random.random() = {val2}")


if __name__ == "__main__":
    main()
