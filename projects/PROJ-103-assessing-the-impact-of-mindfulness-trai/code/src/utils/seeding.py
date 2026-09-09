"""
Random seed pinning for reproducibility.

This module ensures deterministic behavior across numpy, random, and torch
by setting a global seed value (default 42). It provides utilities to set
the seed and verify determinism through repeated execution.
"""

import random
import os
import hashlib
from typing import Optional, Callable, Any

# Try importing torch and numpy; if not available, skip seeding for them
try:
    import numpy as np
    HAS_NUMPY = True
except ImportError:
    HAS_NUMPY = False

try:
    import torch
    HAS_TORCH = True
except ImportError:
    HAS_TORCH = False

DEFAULT_SEED = 42


def set_seed(seed: int = DEFAULT_SEED) -> None:
    """
    Set random seeds for reproducibility across numpy, random, and torch.

    Args:
        seed: Integer seed value. Defaults to 42.
    """
    # Seed the random module
    random.seed(seed)

    # Seed numpy if available
    if HAS_NUMPY:
        np.random.seed(seed)

    # Seed torch if available
    if HAS_TORCH:
        torch.manual_seed(seed)
        # For GPU reproducibility (if available)
        if torch.cuda.is_available():
            torch.cuda.manual_seed(seed)
            torch.cuda.manual_seed_all(seed)
            # Set deterministic algorithms where possible
            torch.backends.cudnn.deterministic = True
            torch.backends.cudnn.benchmark = False

    # Set PYTHONHASHSEED for hash determinism (affects dict/set ordering in older Python)
    os.environ['PYTHONHASHSEED'] = str(seed)


def verify_determinism(
    func: Callable[[], Any],
    seed: int = DEFAULT_SEED,
    iterations: int = 2
) -> bool:
    """
    Verify that a function produces deterministic output when seeded.

    Runs the function multiple times after resetting the seed each time
    and compares the results (via hash) to ensure they are identical.

    Args:
        func: A callable that takes no arguments and returns data.
        seed: The seed value to use.
        iterations: Number of times to run the function.

    Returns:
        True if all runs produce identical output, False otherwise.
    """
    results = []
    for _ in range(iterations):
        set_seed(seed)
        result = func()
        # Convert result to bytes for hashing if possible
        # This is a simplified check; for complex objects, a custom serializer might be needed
        if HAS_NUMPY and hasattr(result, 'tobytes'):
            results.append(hashlib.sha256(result.tobytes()).hexdigest())
        elif isinstance(result, (list, tuple)):
            # Hash string representation for simple collections
            results.append(hashlib.sha256(str(result).encode()).hexdigest())
        else:
            results.append(hashlib.sha256(str(result).encode()).hexdigest())

    # Check if all hashes are identical
    return len(set(results)) == 1


def main() -> None:
    """
    Demonstrate seed pinning and verification.

    This function sets the seed, runs a dummy operation, and verifies
    that the operation is deterministic.
    """
    print(f"Setting seed to {DEFAULT_SEED}...")
    set_seed(DEFAULT_SEED)

    # Example deterministic operation
    def dummy_operation():
        if HAS_NUMPY:
            return np.random.rand(5)
        else:
            return [random.random() for _ in range(5)]

    print("Running dummy operation...")
    result = dummy_operation()
    print(f"Result: {result}")

    print("\nVerifying determinism...")
    is_deterministic = verify_determinism(dummy_operation, DEFAULT_SEED)
    if is_deterministic:
        print("SUCCESS: Output is deterministic.")
    else:
        print("FAILURE: Output is NOT deterministic.")


if __name__ == "__main__":
    main()
