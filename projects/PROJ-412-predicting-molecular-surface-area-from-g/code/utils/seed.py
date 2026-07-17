"""
Seed pinning utility for reproducibility.

This module provides functions to set and verify random seeds across
Python's random module, NumPy, and PyTorch (if available) to ensure
reproducible results in experiments.
"""
import os
import random
import hashlib
from typing import Optional, Dict, Any

import numpy as np

# Try to import torch, but make it optional for environments without it
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

from .logging import get_logger
from .config import get_project_root

logger = get_logger(__name__)

# Default seed value if none provided
DEFAULT_SEED = 42

# Environment variable name for seed
SEED_ENV_VAR = "LLMXIVE_SEED"


def set_seed(seed: Optional[int] = None, deterministic: bool = True) -> int:
    """
    Set random seeds for all relevant libraries to ensure reproducibility.

    Args:
        seed: The seed value to use. If None, reads from environment variable
              or uses DEFAULT_SEED.
        deterministic: If True, sets CuDNN to deterministic mode (slower but
                     reproducible). Only affects PyTorch.

    Returns:
        The seed value that was set.

    Raises:
        ValueError: If the seed is not a non-negative integer.
    """
    if seed is None:
        seed = os.environ.get(SEED_ENV_VAR, DEFAULT_SEED)

    try:
        seed = int(seed)
    except (ValueError, TypeError):
        raise ValueError(f"Seed must be an integer, got {type(seed)}")

    if seed < 0:
        raise ValueError(f"Seed must be non-negative, got {seed}")

    logger.info(f"Setting random seed to {seed}")

    # Python's random module
    random.seed(seed)

    # NumPy
    np.random.seed(seed)

    # PyTorch (if available)
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        torch.cuda.manual_seed_all(seed) if torch.cuda.is_available() else None

        if deterministic and torch.cuda.is_available():
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
    else:
        logger.debug("PyTorch not available, skipping PyTorch seed setting")

    # Set environment variables for PyTorch
    os.environ["PYTHONHASHSEED"] = str(seed)
    if TORCH_AVAILABLE and torch.cuda.is_available():
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8"

    return seed


def get_seed_from_env() -> Optional[int]:
    """
    Retrieve the seed value from the environment variable.

    Returns:
        The seed value as an integer if set, None otherwise.
    """
    seed_str = os.environ.get(SEED_ENV_VAR)
    if seed_str is None:
        return None
    try:
        return int(seed_str)
    except ValueError:
        logger.warning(f"Invalid seed value in environment: {seed_str}")
        return None


def verify_seed_reproducibility(seed: int, n_iterations: int = 3) -> Dict[str, Any]:
    """
    Verify that the seed produces reproducible results.

    This function runs a simple random operation multiple times and checks
    if the results are identical when the seed is reset.

    Args:
        seed: The seed to verify.
        n_iterations: Number of times to run the verification test.

    Returns:
        A dictionary with verification results.
    """
    results = []

    for i in range(n_iterations):
        # Reset seed
        set_seed(seed)

        # Generate a random number
        val_py = random.random()
        val_np = np.random.random()

        if TORCH_AVAILABLE:
            val_torch = torch.rand(1).item()
        else:
            val_torch = None

        results.append({
            "iteration": i,
            "python": val_py,
            "numpy": val_np,
            "torch": val_torch
        })

    # Check reproducibility
    python_values = [r["python"] for r in results]
    numpy_values = [r["numpy"] for r in results]
    torch_values = [r["torch"] for r in results if r["torch"] is not None]

    reproducibility = {
        "python": len(set(python_values)) == 1,
        "numpy": len(set(numpy_values)) == 1,
        "torch": len(set(torch_values)) == 1 if torch_values else True
    }

    all_reproducible = all(reproducibility.values())

    logger.info(f"Seed reproducibility check: {'PASSED' if all_reproducible else 'FAILED'}")
    for lib, passed in reproducibility.items():
        logger.debug(f"  {lib}: {'reproducible' if passed else 'NOT reproducible'}")

    return {
        "seed": seed,
        "n_iterations": n_iterations,
        "all_reproducible": all_reproducible,
        "details": reproducibility,
        "sample_values": results[0]
    }


def generate_seed_hash(seed: int) -> str:
    """
    Generate a deterministic hash for a given seed.

    Args:
        seed: The seed value.

    Returns:
        A hexadecimal string hash of the seed.
    """
    return hashlib.sha256(str(seed).encode()).hexdigest()[:16]


def seed_context(seed: Optional[int] = None):
    """
    Context manager for temporarily setting and restoring seeds.

    Args:
        seed: The seed to use within the context. If None, uses DEFAULT_SEED.

    Example:
        with seed_context(123):
            # Code here uses seed 123
            result = some_random_function()
        # Seed is restored to previous state after context
    """
    class SeedContext:
        def __init__(self, seed_val):
            self.seed_val = seed_val if seed_val is not None else DEFAULT_SEED
            self.old_seed = None

        def __enter__(self):
            self.old_seed = get_seed_from_env()
            set_seed(self.seed_val)
            return self.seed_val

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.old_seed is not None:
                set_seed(self.old_seed)
            return False

    return SeedContext(seed)