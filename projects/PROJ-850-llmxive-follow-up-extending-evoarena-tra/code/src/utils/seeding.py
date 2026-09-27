import random
import os
import numpy as np
import torch
from typing import Optional

DEFAULT_SEED = 42

def set_deterministic_seed(seed: Optional[int] = None) -> None:
    """
    Configure deterministic random seeds for the entire project to ensure
    reproducible execution across runs.

    This function sets seeds for:
    - Python's built-in random module
    - NumPy
    - PyTorch (CPU and GPU if available)
    - Environment variables for CUDA determinism

    Args:
        seed: The seed value to use. Defaults to DEFAULT_SEED (42) if None.
    """
    if seed is None:
        seed = DEFAULT_SEED

    # Set Python random seed
    random.seed(seed)

    # Set NumPy random seed
    np.random.seed(seed)

    # Set PyTorch seeds
    torch.manual_seed(seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)  # for multi-GPU

    # Set environment variables for deterministic behavior (if applicable)
    os.environ["PYTHONHASHSEED"] = str(seed)

    # PyTorch specific settings for reproducibility
    # Note: These may impact performance, but ensure reproducibility
    torch.backends.cudnn.deterministic = True
    torch.backends.cudnn.benchmark = False

    # Log the seed value for transparency
    print(f"[Seeding] Deterministic seed set to: {seed}")

def get_seed_value() -> int:
    """
    Returns the default seed value used by the project.

    Returns:
        int: The default seed value (42).
    """
    return DEFAULT_SEED
