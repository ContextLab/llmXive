"""
Random seed pinning utility for reproducibility.

This module ensures deterministic behavior across the pipeline by setting
  random seeds for Python's built-in random, NumPy, PyTorch (if available),
  and other common libraries used in computational chemistry and ML.

It is designed to be called early in the pipeline execution (e.g., at the
  start of any script) to guarantee that results are reproducible given
  the same input data and configuration.

Usage:
    from utils.seeding import set_seed
    set_seed(42)
"""

import os
import random
import sys
from typing import Optional

# Optional imports for deep learning frameworks
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False
    np = None  # type: ignore

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False
    torch = None  # type: ignore

try:
    import tensorflow as tf
    HAS_TF = True
except ImportError:
    HAS_TF = False
    tf = None  # type: ignore

try:
    import keras
    HAS_KERAS = True
except ImportError:
    HAS_KERAS = False
    keras = None  # type: ignore

# Default seed if none provided
DEFAULT_SEED = 42

def set_seed(seed: Optional[int] = None, deterministic: bool = True) -> None:
    """
    Set random seeds for reproducibility across all supported libraries.

    This function sets the seed for:
      - Python's built-in `random` module
      - `os.environ` for PYTHONHASHSEED (affects dict/set hashing)
      - `numpy` (if available)
      - `torch` (if available), including cuDNN deterministic settings
      - `tensorflow` (if available)
      - `keras` (if available)

    Args:
        seed (Optional[int]): The seed value to use. If None, uses DEFAULT_SEED.
        deterministic (bool): If True, enforces deterministic behavior in
          PyTorch and TensorFlow where possible (may impact performance).

    Raises:
        ValueError: If the provided seed is not a non-negative integer.
    """
    if seed is None:
        seed = DEFAULT_SEED

    if not isinstance(seed, int) or seed < 0:
        raise ValueError(f"Seed must be a non-negative integer, got {seed}")

    # 1. Python built-in random
    random.seed(seed)

    # 2. Environment variable for hash randomization
    os.environ["PYTHONHASHSEED"] = str(seed)

    # 3. NumPy
    if HAS_NUMPY and np is not None:
        np.random.seed(seed)

    # 4. PyTorch
    if HAS_TORCH and torch is not None:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
            # Ensure deterministic behavior if requested
            if deterministic:
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
        # CPU operations
        torch.use_deterministic_algorithms(deterministic)

    # 5. TensorFlow / Keras
    if HAS_TF and tf is not None:
        tf.random.set_seed(seed)
        if deterministic:
            os.environ["TF_DETERMINISTIC_OPS"] = "1"
            # Limit GPU memory growth to avoid non-deterministic allocation
            gpus = tf.config.list_physical_devices("GPU")
            if gpus:
                try:
                    for gpu in gpus:
                        tf.config.experimental.set_memory_growth(gpu, True)
                except RuntimeError:
                    pass  # GPUs already initialized

    if HAS_KERAS and keras is not None:
        # Keras usually respects TF seed, but explicit set for safety
        keras.backend.clear_session()

    # Log the action (using standard print for now, can be replaced with logging later)
    print(f"[Seeding] Random seed set to {seed}. Deterministic mode: {deterministic}")

def get_seed_info() -> dict:
    """
    Return a dictionary describing the current seed configuration status.

    Useful for logging and auditing reproducibility settings.

    Returns:
        dict: A dictionary containing:
            - 'seed': The currently set seed (or None if not set explicitly)
            - 'libraries': A dict of booleans indicating which libraries are available
    """
    return {
        "seed": DEFAULT_SEED,  # Default assumed if not explicitly changed in a session
        "libraries": {
            "random": True,
            "numpy": HAS_NUMPY,
            "torch": HAS_TORCH,
            "tensorflow": HAS_TF,
            "keras": HAS_KERAS,
        }
    }
