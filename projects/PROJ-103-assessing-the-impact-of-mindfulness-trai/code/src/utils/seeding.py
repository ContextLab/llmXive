"""
Random seed pinning for reproducibility.

This module provides a small, well‑tested API used throughout the project
and by the unit‑tests in ``tests/unit/test_seeding.py``.  The design is
deliberately simple: a single global seed (default 42) can be set for the
standard library ``random`` module, NumPy, and (optionally) PyTorch.  The
``verify_determinism`` helper runs a user‑provided zero‑argument function
multiple times under the same seed and raises ``RuntimeError`` if any
variation is observed – this matches the expectations of the test suite.
"""

import os
import random
import hashlib
from typing import Callable, Any, Optional

# ----------------------------------------------------------------------
# Optional imports – the environment may not have these packages installed.
# ----------------------------------------------------------------------
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:  # pragma: no cover – NumPy is always available in the CI image.
    HAS_NUMPY = False

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:  # pragma: no cover
    TORCH_AVAILABLE = False

# ----------------------------------------------------------------------
# Public constants
# ----------------------------------------------------------------------
DEFAULT_SEED: int = 42

# ----------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------
def set_all_seeds(seed: Optional[int] = DEFAULT_SEED) -> None:
    """
    Set the global random seed for reproducibility across supported libraries.

    Parameters
    ----------
    seed : int or None, optional
        Seed value to use.  If ``None`` is supplied the ``DEFAULT_SEED`` is
        used.  The function is idempotent – calling it multiple times with
        the same seed yields identical random streams.
    """
    if seed is None:
        seed = DEFAULT_SEED

    # Python's built‑in RNG
    random.seed(seed)

    # NumPy RNG (if available)
    if HAS_NUMPY:
        np.random.seed(seed)

    # PyTorch RNG (if available)
    if TORCH_AVAILABLE:
        torch.manual_seed(seed)
        if torch.cuda.is_available():
            torch.cuda.manual_seed_all(seed)

        # Ensure deterministic CUDA behaviour
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False

    # Hash‑randomisation seed – makes dict/set ordering deterministic
    os.environ["PYTHONHASHSEED"] = str(seed)

def get_seed() -> int:
    """
    Return the current default seed value.

    The test‑suite checks that the default is ``42`` and that the function
    mirrors the constant.
    """
    return DEFAULT_SEED

def verify_determinism(
    func: Callable[[], Any],
    seed: int = DEFAULT_SEED,
    iterations: int = 2,
) -> bool:
    """
    Verify that a zero‑argument callable produces identical output across
    repeated executions with the same random seed.

    The function hashes each result (using SHA‑256) and compares the hashes.
    If any hash differs a ``RuntimeError`` is raised – this behaviour is
    required by ``tests/unit/test_seeding.py``.  When all hashes match the
    function returns ``True``.

    Parameters
    ----------
    func : Callable[[], Any]
        The function to test.  It must not accept any arguments.
    seed : int, optional
        Seed to set before each invocation (default ``DEFAULT_SEED``).
    iterations : int, optional
        Number of repetitions (default 2).

    Returns
    -------
    bool
        ``True`` if all runs produced identical output.

    Raises
    ------
    RuntimeError
        If the outputs differ across runs.
    """
    if iterations < 2:
        raise ValueError("verify_determinism requires at least two iterations")

    hashes = []
    for _ in range(iterations):
        set_all_seeds(seed)
        result = func()

        # Convert the result to a deterministic byte representation.
        if HAS_NUMPY and hasattr(result, "tobytes"):
            data_bytes = result.tobytes()
        elif isinstance(result, (list, tuple, dict, set)):
            # ``repr`` gives a stable string for simple containers.
            data_bytes = repr(result).encode()
        else:
            data_bytes = str(result).encode()

        hashes.append(hashlib.sha256(data_bytes).hexdigest())

    if len(set(hashes)) != 1:
        raise RuntimeError("Function output is not deterministic")
    return True

# ----------------------------------------------------------------------
# Demo entry‑point (not used by the tests but kept for completeness)
# ----------------------------------------------------------------------
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
