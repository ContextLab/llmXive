"""
Deterministic seeding utilities for reproducible experiments.
"""
import random
import os
import numpy as np
import torch
import hashlib

def set_seed(seed: int = 42) -> None:
    """
    Set random seeds for reproducibility across all libraries.
    
    This function ensures deterministic behavior for:
    - Python's built-in random module
    - NumPy random number generation
    - PyTorch CPU and GPU operations (if available)
    - Environment variables affecting hashing
    
    Args:
        seed: Integer seed value for reproducibility. Defaults to 42.
    """
    # Set Python random seed
    random.seed(seed)
    
    # Set environment variable for hash randomization
    os.environ["PYTHONHASHSEED"] = str(seed)
    
    # Set NumPy random seed
    np.random.seed(seed)
    
    # Set PyTorch random seeds
    torch.manual_seed(seed)
    
    # GPU-specific seeds if CUDA is available
    if torch.cuda.is_available():
        torch.cuda.manual_seed(seed)
        torch.cuda.manual_seed_all(seed)
        # Ensure deterministic behavior in CuDNN
        torch.backends.cudnn.deterministic = True
        torch.backends.cudnn.benchmark = False
    
    # Additional determinism settings for PyTorch
    # These ensure that operations are deterministic even on GPU
    torch.use_deterministic_algorithms(True)
    
    # Log the seed for auditability
    logger_name = "seed_utils"
    # Import logger dynamically to avoid circular imports if needed
    # But since logger.py is a sibling, we can try to import
    try:
        from utils.logger import get_logger
        logger = get_logger(logger_name)
        logger.info(f"Random seed set to {seed}. Deterministic mode enabled.")
    except ImportError:
        # Fallback to print if logger is not ready
        print(f"Random seed set to {seed}. Deterministic mode enabled.")