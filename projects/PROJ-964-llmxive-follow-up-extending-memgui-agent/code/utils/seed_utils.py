"""
Deterministic random seed utilities for reproducible synthetic generation.

This module centralizes all seeding logic to ensure that synthetic data
generation, model inference, and evaluation steps are fully reproducible
across different runs and environments.

It integrates with the existing `code/utils/config.py` module to manage
project paths and environment variables.
"""

import os
import random
import hashlib
from typing import Optional, Dict, Any, List

import numpy as np

# Optional: Check for torch availability without hard dependency
# We import inside functions to avoid failing if torch is not installed
# but the project requirements.txt lists it, so it should be present.
try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import transformers
    TRANSFORMERS_AVAILABLE = True
except ImportError:
    TRANSFORMERS_AVAILABLE = False

from utils.config import get_project_root, get_env_variable


def set_deterministic_seeds(seed: int = 42) -> Dict[str, Any]:
    """
    Set random seeds for Python's random, NumPy, and PyTorch (if available)
    to ensure reproducible results.

    This function configures:
    - Python's built-in `random` module
    - `numpy` random state
    - `torch` random state, CUDA states, and benchmark settings (if available)
    - `transformers` random state (if available)

    Args:
        seed (int): The integer seed value to use. Defaults to 42.

    Returns:
        Dict[str, Any]: A dictionary containing the applied seed and a status
                        of which libraries were successfully seeded.
    """
    results = {
        "seed": seed,
        "python": False,
        "numpy": False,
        "torch": False,
        "transformers": False,
        "cudnn_deterministic": False,
    }

    # 1. Python Random
    random.seed(seed)
    results["python"] = True

    # 2. NumPy
    np.random.seed(seed)
    results["numpy"] = True

    # 3. PyTorch (if available)
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)  # if multi-GPU
            # Ensure deterministic behavior in CUDA
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False
            results["cudnn_deterministic"] = True
        results["torch"] = True

    # 4. Transformers (if available)
    # Transformers library often respects the global torch seed, but
    # some operations (like tokenization shuffling) might need explicit handling.
    # We ensure the environment variable is set for reproducibility.
    if TRANSFORMERS_AVAILABLE:
        # Hugging Face datasets and trainers often check this env var
        os.environ["CUBLAS_WORKSPACE_CONFIG"] = ":4096:8" if TORCH_AVAILABLE else ""
        os.environ["PYTHONHASHSEED"] = str(seed)
        results["transformers"] = True

    return results


def get_reproducible_seed_from_string(seed_string: str, max_seed: int = 2**32 - 1) -> int:
    """
    Generate a deterministic integer seed from a string input.

    This is useful for generating specific seeds for different experiments
    or data splits based on a descriptive string (e.g., "US1-Run-A"),
    ensuring that the same string always yields the same seed.

    Args:
        seed_string (str): The string to hash.
        max_seed (int): The maximum value for the seed (default: 2^32 - 1).

    Returns:
        int: A deterministic integer seed in the range [0, max_seed].
    """
    if not isinstance(seed_string, str):
        raise TypeError("seed_string must be a string")

    # Use SHA-256 for a robust hash
    hash_object = hashlib.sha256(seed_string.encode('utf-8'))
    hash_hex = hash_object.hexdigest()

    # Convert the first 8 hex characters (32 bits) to an integer
    seed_int = int(hash_hex[:8], 16)

    return seed_int % (max_seed + 1)


def ensure_seed_environment(seed: Optional[int] = None) -> int:
    """
    Ensure a deterministic seed is set, either from an argument or environment variable.

    This function checks for the `LLMXIVE_SEED` environment variable.
    If provided, it uses that value. If not, it uses the provided argument.
    If neither is provided, it defaults to 42.

    This allows for easy overriding of seeds via environment configuration
    without changing code.

    Args:
        seed (Optional[int]): An explicit seed value.

    Returns:
        int: The seed value that was set.
    """
    env_seed = get_env_variable("LLMXIVE_SEED", default=None)

    if env_seed is not None:
        try:
            final_seed = int(env_seed)
            print(f"Using seed from environment variable LLMXIVE_SEED: {final_seed}")
        except ValueError:
            raise ValueError(f"Invalid seed value in LLMXIVE_SEED: '{env_seed}'. Must be an integer.")
    elif seed is not None:
        final_seed = seed
    else:
        final_seed = 42

    set_deterministic_seeds(final_seed)
    return final_seed
