"""
Random seed pinning for reproducibility.

This module provides a small, well‑tested API used throughout the project
and by the unit‑tests in ``tests/unit/test_seeding.py``.
"""

import os
import random
import hashlib
from typing import Callable, Any, Optional

try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

DEFAULT_SEED: int = 42

def set_all_seeds(seed: Optional[int] = DEFAULT_SEED) -> None:
    """Set the global random seed for reproducibility across supported libraries."""
    if seed is None:
        seed = DEFAULT_SEED

    random.seed(seed)

    if HAS_NUMPY:
        np.random.seed(seed)

    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    os.environ["PYTHONHASHSEED"] = str(seed)

def get_seed() -> int:
    """Return the current default seed value."""
    return DEFAULT_SEED

def verify_determinism(
    func: Callable[[], Any],
    seed: int = DEFAULT_SEED,
    iterations: int = 2,
) -> bool:
    """
    Verify that a zero‑argument callable produces identical output across
    repeated executions with the same random seed.
    """
    if iterations < 2:
        raise ValueError("verify_determinism requires at least two iterations")

    hashes = []
    for _ in range(iterations):
        set_all_seeds(seed)
        result = func()

        if HAS_NUMPY and hasattr(result, "tobytes"):
            data_bytes = result.tobytes()
        elif isinstance(result, (list, tuple, dict, set)):
            data_bytes = repr(result).encode()
        else:
            data_bytes = str(result).encode()

        hashes.append(hashlib.sha256(data_bytes).hexdigest())

    if len(set(hashes)) != 1:
        raise RuntimeError("Function output is not deterministic")
    return True

def main() -> None:
    """Simple demonstration of the seeding utilities."""
    print(f"Setting seed to {DEFAULT_SEED}...")
    set_all_seeds(DEFAULT_SEED)

    def dummy():
        if HAS_NUMPY:
            return np.random.rand(5)
        return [random.random() for _ in range(5)]

    print("Running dummy operation...")
    print(dummy())

    print("Verifying determinism...")
    deterministic = verify_determinism(dummy, DEFAULT_SEED)
    print("Deterministic:", deterministic)

if __name__ == "__main__":
    main()
