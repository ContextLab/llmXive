"""
Example module demonstrating the seed pinning pattern (Task T060).

This file serves as a template for all code modules in the project.
Every module MUST call set_global_seed(12345) immediately after imports.

Usage:
    import seed_pinning_example
    # The seed is already set at module import time
"""
# ============================================================================
# REQUIRED: Import and call set_global_seed at the start of EVERY module
# ============================================================================
from pipeline.utils import set_global_seed

# Call immediately after imports - this is the T060 requirement
set_global_seed(12345)
# ============================================================================

"""
Example module for demonstrating seed pinning pattern.

This module shows the correct pattern that ALL code modules must follow:
1. Import set_global_seed from pipeline.utils
2. Call set_global_seed(12345) immediately after imports
3. This ensures reproducible random number generation

For more information, see task T060 in tasks.md.
"""
import random
import numpy as np


def generate_example_data(n_samples=100):
    """
    Generate example random data demonstrating seed reproducibility.

    Args:
        n_samples (int): Number of samples to generate

    Returns:
        tuple: (random_list, numpy_array)
    """
    # These will be reproducible due to set_global_seed(12345) at module start
    random_list = [random.random() for _ in range(n_samples)]
    numpy_array = np.random.randn(n_samples)

    return random_list, numpy_array


def main():
    """Demonstrate seed pinning in action."""
    print("Running seed pinning example...")
    print(f"Random value 1: {random.random()}")

    # Reset seed and show it's reproducible
    set_global_seed(12345)
    print(f"Random value 2 (after reset): {random.random()}")

    # Generate example data
    r_list, n_array = generate_example_data(5)
    print(f"Random list (first 5): {r_list[:5]}")
    print(f"NumPy array (first 5): {n_array[:5]}")


if __name__ == '__main__':
    main()