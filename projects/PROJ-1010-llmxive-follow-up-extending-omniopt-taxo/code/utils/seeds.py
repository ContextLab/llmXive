"""
Seed pinning utility for reproducible experiments in the llmXive pipeline.

This module provides functions to set random seeds across all relevant libraries
(Python, NumPy, PyTorch, and optionally TensorFlow) to ensure deterministic
behavior during research execution.
"""

import os
import random
import hashlib
from typing import Optional, Dict, Any

# Attempt to import numpy and torch; they are required dependencies per requirements.txt
import numpy as np

try:
    import torch
    TORCH_AVAILABLE = True
except ImportError:
    TORCH_AVAILABLE = False

try:
    import tensorflow as tf
    TF_AVAILABLE = True
except ImportError:
    TF_AVAILABLE = False


def set_seed(seed: int = 42, deterministic: bool = True) -> Dict[str, Any]:
    """
    Set random seeds for all supported libraries to ensure reproducibility.

    Args:
        seed (int): The random seed integer to use. Default is 42.
        deterministic (bool): If True, forces deterministic algorithms in PyTorch
            (e.g., cuDNN). Note: This may reduce performance.

    Returns:
        Dict[str, Any]: A dictionary containing the seed value and a status report
            of which libraries were successfully seeded.
    """
    status = {
        "seed": seed,
        "deterministic_mode": deterministic,
        "libraries_seeded": [],
        "errors": []
    }

    # Set Python standard library random
    random.seed(seed)
    status["libraries_seeded"].append("random")

    # Set NumPy
    np.random.seed(seed)
    status["libraries_seeded"].append("numpy")

    # Set PyTorch
    if TORCH_AVAILABLE:
        try:
            torch.manual_seed(seed)
            if torch.cuda.is_available():
                torch.cuda.manual_seed(seed)
                torch.cuda.manual_seed_all(seed)  # if multi-GPU

            if deterministic:
                torch.backends.cudnn.deterministic = True
                torch.backends.cudnn.benchmark = False
                # Note: Setting deterministic=True in PyTorch may raise errors
                # for some operations. We catch and log here if needed, but
                # typically this is set globally.
            status["libraries_seeded"].append("torch")
        except Exception as e:
            status["errors"].append(f"PyTorch seeding failed: {str(e)}")
    else:
        status["errors"].append("PyTorch not available, skipping torch seeding")

    # Set TensorFlow if available
    if TF_AVAILABLE:
        try:
            tf.random.set_seed(seed)
            status["libraries_seeded"].append("tensorflow")
        except Exception as e:
            status["errors"].append(f"TensorFlow seeding failed: {str(e)}")
    else:
        status["errors"].append("TensorFlow not available, skipping TF seeding")

    # Set environment variable for some libraries that respect it
    os.environ["PYTHONHASHSEED"] = str(seed)

    return status


def get_seed_from_hash(data: str, max_seed: int = 2**32 - 1) -> int:
    """
    Generate a deterministic seed integer from an input string.

    This is useful for generating seeds based on experiment names or configuration
    strings to ensure the same configuration always yields the same seed.

    Args:
        data (str): The input string to hash.
        max_seed (int): The maximum possible seed value (inclusive).

    Returns:
        int: A deterministic integer seed in the range [0, max_seed].
    """
    hash_obj = hashlib.sha256(data.encode('utf-8'))
    hash_int = int(hash_obj.hexdigest(), 16)
    return hash_int % (max_seed + 1)


def restore_seed(state: Dict[str, Any]) -> None:
    """
    Restore random states from a previously saved state dictionary.

    Note: This implementation assumes the state was created by a compatible
    version of this module. It primarily resets the global seeds. For full
    state restoration (e.g., generator states), one would need to pickle
    the generator objects themselves, which is not standard across libraries.

    Args:
        state (Dict[str, Any]): A dictionary containing 'seed' and potentially
            other state information.
    """
    if "seed" not in state:
        raise ValueError("Invalid state dictionary: missing 'seed' key")
    set_seed(seed=state["seed"], deterministic=state.get("deterministic_mode", True))


def main() -> None:
    """
    CLI entry point for testing the seed utility.
    """
    print("llmXive Seed Utility")
    print("-" * 30)

    # Test with default seed
    print("Setting default seed (42)...")
    status = set_seed(seed=42)
    print(f"Status: {status}")

    # Test hash-based seed generation
    print("\nGenerating seed from string 'experiment_alpha'...")
    seed_val = get_seed_from_hash("experiment_alpha")
    print(f"Generated seed: {seed_val}")

    # Test setting that seed
    print(f"Setting seed {seed_val}...")
    status = set_seed(seed=seed_val)
    print(f"Status: {status}")

    # Verify reproducibility
    print("\nVerifying reproducibility (generating 3 random numbers)...")
    val1 = random.random()
    n1 = np.random.rand()
    t1 = torch.rand(1).item() if TORCH_AVAILABLE else None

    print(f"Run 1: random={val1:.6f}, numpy={n1:.6f}, torch={t1}")

    # Reset and generate again
    set_seed(seed=seed_val)
    val2 = random.random()
    n2 = np.random.rand()
    t2 = torch.rand(1).item() if TORCH_AVAILABLE else None

    print(f"Run 2: random={val2:.6f}, numpy={n2:.6f}, torch={t2}")

    assert abs(val1 - val2) < 1e-9, "Random seed failed for Python random"
    assert abs(n1 - n2) < 1e-9, "Random seed failed for NumPy"
    if TORCH_AVAILABLE:
        assert t1 is not None and t2 is not None and abs(t1 - t2) < 1e-9, "Random seed failed for PyTorch"

    print("\nReproducibility verified successfully.")


if __name__ == "__main__":
    main()